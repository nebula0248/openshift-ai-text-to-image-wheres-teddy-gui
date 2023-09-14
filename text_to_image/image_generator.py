import os
import json
import threading

import math
import torch
import numpy as np
from diffusers import DDIMScheduler
from transformers import CLIPTokenizer
from tqdm.auto import tqdm
from PIL import Image

import grpc
from text_to_image import grpc_predict_v2_pb2, grpc_predict_v2_pb2_grpc
from utils import storage

grpc_host = os.environ.get('GRPC_HOST', 'modelmesh-serving')
grpc_port = int(os.environ.get('GRPC_PORT', '8033'))
textencoder_model_name = os.environ.get('TEXTENCODER_MODEL_NAME', 'textencoder')
unet_model_name = os.environ.get('UNET_MODEL_NAME', 'unet')
vaeencoder_model_name = os.environ.get('VAEENCODER_MODEL_NAME', 'vaeencoder')
vaedecoder_model_name = os.environ.get('VAEDECODER_MODEL_NAME', 'vaedecoder')

channel = grpc.insecure_channel(f"{grpc_host}:{grpc_port}")
stub = grpc_predict_v2_pb2_grpc.GRPCInferenceServiceStub(channel)


tokenizer = CLIPTokenizer.from_pretrained("cfchase/stable-diffusion-rhteddy", subfolder="tokenizer")


def vae_decoder(latent_sample):
    inputs = []
    inputs.append(grpc_predict_v2_pb2.ModelInferRequest().InferInputTensor())
    inputs[0].name = "latent_sample"
    inputs[0].datatype = "FP32"
    inputs[0].shape.extend([1, 4, 64, 64])
    arr = latent_sample.flatten()
    inputs[0].contents.fp32_contents.extend(arr)

    request = grpc_predict_v2_pb2.ModelInferRequest()
    request.model_name = vaedecoder_model_name
    request.inputs.extend(inputs)

    response = stub.ModelInfer(request)
    out_sample = np.frombuffer(response.raw_output_contents[0], dtype=np.float32)

    return torch.tensor(out_sample.reshape([1, 3, 512, 512]))


def textencoder(input_arr):
    inputs = []
    inputs.append(grpc_predict_v2_pb2.ModelInferRequest().InferInputTensor())
    inputs[0].name = "input_ids"
    inputs[0].datatype = "INT32"
    inputs[0].shape.extend([1, 77])
    arr = input_arr.flatten()
    inputs[0].contents.int_contents.extend(arr)

    request = grpc_predict_v2_pb2.ModelInferRequest()
    request.model_name = textencoder_model_name
    request.inputs.extend(inputs)

    response = stub.ModelInfer(request)
    text_embeddings = np.frombuffer(response.raw_output_contents[0], dtype=np.float32)

    return torch.tensor(text_embeddings.reshape([-1, 77, 768]), dtype=torch.float32)


def unet(encoder_hidden_states, timestep, sample):
    inputs = []
    inputs.append(grpc_predict_v2_pb2.ModelInferRequest().InferInputTensor())
    inputs[0].name = "encoder_hidden_states"
    inputs[0].datatype = "FP32"
    inputs[0].shape.extend([2, 77, 768])
    arr = encoder_hidden_states.flatten()
    inputs[0].contents.fp32_contents.extend(arr)

    inputs.append(grpc_predict_v2_pb2.ModelInferRequest().InferInputTensor())
    inputs[1].name = "timestep"
    inputs[1].datatype = "INT64"
    inputs[1].shape.extend([2, 1])
    arr = timestep.flatten()
    inputs[1].contents.int64_contents.extend(arr)

    inputs.append(grpc_predict_v2_pb2.ModelInferRequest().InferInputTensor())
    inputs[2].name = "sample"
    inputs[2].datatype = "FP32"
    inputs[2].shape.extend([2, 4, 64, 64])
    arr = sample.flatten()
    inputs[2].contents.fp32_contents.extend(arr)

    request = grpc_predict_v2_pb2.ModelInferRequest()
    request.model_name = unet_model_name
    request.inputs.extend(inputs)

    response = stub.ModelInfer(request)
    out_sample = np.frombuffer(response.raw_output_contents[0], dtype=np.float32)

    return torch.tensor(out_sample.reshape([-1, 4, 64, 64]), dtype=torch.float32)


class ImageGenerator:
    def __init__ (self, prediction_id, image_id, prompt):
        self.prediction_id = prediction_id
        self.image_id = image_id
        self.prompt = prompt
        self.image_json = {
            "status": "QUEUED",
            "progress": 0,
            "prompt": prompt,
            "file": f"/api/images/{self.prediction_id}/image-{self.image_id}.jpg"
        }
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def write_image_json(self, status, progress):
        if status:
            self.image_json["status"] = status
        if progress is not None:
            self.image_json["progress"] = progress

        json_file = os.path.join(self.prediction_id, f"image-{self.image_id}.json")
        storage.write_json(self.image_json, json_file)


    def run_inference_pipeline(self):
        scheduler = DDIMScheduler.from_pretrained("cfchase/stable-diffusion-rhteddy", subfolder="scheduler")
        torch_device = "cpu"
        prompt = [self.prompt]
        height = 512  # default height of Stable Diffusion
        width = 512  # default width of Stable Diffusion
        num_inference_steps = 50  # Number of denoising steps
        guidance_scale = 7.5  # Scale for classifier-free guidance

        # Seed generator to create the inital latent noise
        # generator = torch.manual_seed(0)  # manual
        generator = torch.Generator()
        generator.seed()  # random

        batch_size = len(prompt)

        text_input = tokenizer(
            prompt, padding="max_length", max_length=tokenizer.model_max_length, truncation=True, return_tensors="pt"
        )

        with torch.no_grad():
            text_encoder_args = text_input.input_ids.to(torch_device)
            text_embeddings = textencoder(text_input.input_ids.numpy())

        max_length = text_input.input_ids.shape[-1]
        uncond_input = tokenizer([""] * batch_size, padding="max_length", max_length=max_length, return_tensors="pt")
        uncond_embeddings = textencoder(uncond_input.input_ids.numpy())
        text_embeddings = torch.cat([uncond_embeddings, text_embeddings])

        latents = torch.randn(
            #(batch_size, unet.in_channels, height // 8, width // 8),
            (batch_size, 4, height // 8, width // 8),
            generator=generator,
        )
        latents = latents.to(torch_device)

        scheduler.set_timesteps(num_inference_steps)

        i = 0
        for t in tqdm(scheduler.timesteps):
            # expand the latents if we are doing classifier-free guidance to avoid doing two forward passes.
            latent_model_input = torch.cat([latents] * 2)

            latent_model_input = scheduler.scale_model_input(latent_model_input, timestep=t)

            # torch.tensor([t, t]) instead of t to workaround batch error on triton grpc
            noise_pred = unet(text_embeddings, torch.tensor([t, t]), latent_model_input)

            # perform guidance
            noise_pred_uncond, noise_pred_text = noise_pred.chunk(2)
            noise_pred = noise_pred_uncond + guidance_scale * (noise_pred_text - noise_pred_uncond)

            # compute the previous noisy sample x_t -> x_t-1
            latents = scheduler.step(noise_pred, t, latents).prev_sample
            i += 1
            if i % 5 == 0:
                self.write_image_json(None, math.floor(i / num_inference_steps * 99))


        # scale and decode the image latents with vae
        latents = 1 / 0.18215 * latents
        image = vae_decoder(latents)

        image = (image / 2 + 0.5).clamp(0, 1).squeeze()
        image = (image.permute(1, 2, 0) * 255).to(torch.uint8).cpu().numpy()
        images = (image * 255).round().astype("uint8")
        image = Image.fromarray(image)
        storage.write_image(image, os.path.join(self.prediction_id, f"image-{self.image_id}.jpg"))

    def run(self):
        print(f"Running image generator {self.prediction_id}/image-{self.image_id} on prompt {self.prompt}")
        self.write_image_json("IN_PROGRESS", 0)
        self.run_inference_pipeline()
        self.write_image_json("COMPLETE", 100)


