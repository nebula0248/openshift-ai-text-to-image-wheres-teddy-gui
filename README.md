# Where's Teddy (for OpenShift AI text-to-image demo)

This is the frontend GUI for the OpenShift AI text-to-image demo (i.e. stable diffusion) which generate Teddy images. To run this, simply copy the Git URL here, and use "Deploy by Git" method to build the app on OpenShift. Remember to select "devfile" as the build type.

Some known issues:
- The default memory setting may be too low. You may need to manually adjust the request & limit setting of the pod that runs.
- The default K8S service that is being deployed seems have incorrect label, need to manually fix it.
