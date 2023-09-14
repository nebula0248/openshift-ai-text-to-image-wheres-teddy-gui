import * as React from 'react';
import {
  Button,
  Gallery,
  GalleryItem,
  PageSection,
  Progress,
  ProgressSize,
  Stack,
  StackItem,
  TextContent,
  Text,
} from '@patternfly/react-core';

import './Album.css';
import { useParams } from 'react-router';
import { useHistory } from 'react-router-dom';
import { GEN_PHRASE } from '../../constants';

interface GeneratedImage {
  file: string;
  progress: number;
  prompt: string;
  status: string;
}

interface Prediction {
  id: string;
  images: GeneratedImage[];
  prompt: string;
}

const Album: React.FunctionComponent = () => {
  const intervalref = React.useRef<number | null>(null);
  const [prediction, setPrediction] = React.useState(null as Prediction | null);
  const [inProgress, setInProgress] = React.useState(0);
  const [progress, setProgress] = React.useState(0);
  const [galleryItems, setGalleryItems] = React.useState([] as any[]);
  const [intervalId, setIntervalId] = React.useState(null as any);
  const { id } = useParams() as { id: string };
  const history = useHistory();

  async function getAlbum(id: string): Promise<void> {
    if (!id || inProgress) {
      return;
    }

    setInProgress(1);
    const response = await fetch(`/api/predictions/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    setInProgress(0);

    if (!response.ok) {
      throw new Error('Network response was not ok.');
    }

    const responseJson = await response.json();
    setPrediction(responseJson);

    const progressArray = responseJson.images?.map((i) => i.progress).filter((p) => p == 0 || p);
    const minProgress = Math.min(...progressArray);
    setProgress(minProgress);
    setGalleryItems(responseJson.images);
    return responseJson;
  }

  React.useEffect(() => {
    // here's the cleanup function
    console.log({ progress });

    if (progress >= 100) {
      if (intervalref?.current) {
        window.clearInterval(intervalref.current);
      }
      intervalref.current = null;
    }
  }, [progress, intervalref]);

  React.useEffect(() => {
    getAlbum(id);
    intervalref.current = window.setInterval(() => {
      getAlbum(id);
    }, 2000);

    return () => {
      if (intervalref.current !== null) {
        window.clearInterval(intervalref.current);
      }
    };
  }, []);

  const handleReset = () => {
    history.push('/');
  };

  const renderGalleryItem = (g: any, index: number) => {
    let itemContent;

    if (g.status === 'COMPLETE') {
      itemContent = <img src={g.file} alt={`dog image ${index}`} />;
    } else {
      const title = g.status
        ?.toLowerCase()
        .replace('_', ' ')
        .replace(/\b[a-z]/g, function (letter) {
          return letter.toUpperCase();
        });
      itemContent = <Progress value={g.progress} title={title} />;
    }
    return <GalleryItem key={`gallery-item-${index}`}>{itemContent}</GalleryItem>;
  };

  const renderReset = () => {
    if (!galleryItems || galleryItems.length == 0) {
      return null;
    }

    const progressArray = galleryItems?.map((i) => i.progress).filter((p) => p == 0 || p);
    const minProgress = Math.min(...progressArray);

    if (minProgress < 100) {
      return null;
    }

    return (
      <PageSection>
        <Stack hasGutter>
          <StackItem>
            <TextContent>
              <Text component="h1">Teddy is {prediction?.prompt?.replace(GEN_PHRASE, '')}</Text>
            </TextContent>
          </StackItem>
          <StackItem>
            <Button variant="primary" onClick={() => handleReset()}>
              Send him somewhere else
            </Button>
          </StackItem>
        </Stack>
      </PageSection>
    );
  };
  const renderGallery = () => {
    if (!galleryItems || galleryItems.length == 0) {
      return null;
    }
    return (
      <PageSection>
        <Gallery role="list" maxWidths={{ default: '512px' }} hasGutter>
          {galleryItems.map(renderGalleryItem)}
        </Gallery>
      </PageSection>
    );
  };

  return (
    <>
      {renderReset()}
      {renderGallery()}
    </>
  );
};

export { Album };
