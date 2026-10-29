# Deploy in Docker

Build the application in a multi-stage image and run the generic factory in the
final image. The repository's `packaging/Dockerfile` is the reference workflow:

```console
docker build -f packaging/Dockerfile \
  --target webapp \
  --build-arg APPLICATION=my-app \
  -t my-app:local .
```

The runtime container needs both `fastapi-runner` and the application
distribution installed. Set `FASTAPI_RUNNER_APPLICATION` to the distribution
name and use `uvicorn --factory fastapi_runner.entrypoint:app_factory` as the
command. Mount credentials as container secrets rather than baking them into
the image.

Use the repository's Docker Compose configuration for the example application
and the tutorial smoke checks. To validate the tutorial images and run all five
applications locally:

```console
docker compose -f apps/tutorials/compose.yaml up --build
```
