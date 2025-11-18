########################
# 1️⃣ Base image (Alpine)
########################
FROM alpine:3.13 AS base

# ------------------------------------------------------------------
# 1️⃣1️⃣ Copy the `uv` binary from the official image.
#     The binary lives at `/uv` inside the source image; we place it
#     in `/usr/local/bin` where it is on the PATH.
# ------------------------------------------------------------------
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# ------------------------------------------------------------------
# 1️⃣2️⃣ Install runtime packages we need later (git + bash)
# ------------------------------------------------------------------
RUN apk update && \
    apk add --no-cache git bash

# ------------------------------------------------------------------
# 1️⃣3️⃣ Environment variables that affect Python/uv behaviour
# ------------------------------------------------------------------
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# ------------------------------------------------------------------
# 1️⃣4️⃣ Create a non‑root user that will run the app
# ------------------------------------------------------------------
ARG KEDRO_UID=999
ARG KEDRO_GID=1000

RUN addgroup -g "${KEDRO_GID}" kedro_group && \
    adduser -D -h /home/kedro_user -s /bin/bash -G kedro_group -u "${KEDRO_UID}" kedro_user

# ------------------------------------------------------------------
# 1️⃣5️⃣ Create the application directory and give ownership to the user
# ------------------------------------------------------------------
RUN mkdir -p /usr/app && \
    chown -R kedro_user:kedro_group /usr/app

WORKDIR /usr/app


#################################
# 2️⃣ Builder stage (dependencies)
#################################
FROM base AS builder

# ------------------------------------------------------------------
# 2️⃣1️⃣ Install the project's Python dependencies using uv.
#       The `--mount` flags give us a persistent cache and bind the
#       lockfile / pyproject / packages directory from the host.
# ------------------------------------------------------------------
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=packages,target=packages,rw \
    uv sync --locked --no-install-workspace --no-dev


##########################
# 3️⃣ Final image (runtime)
##########################
FROM base AS final

# ------------------------------------------------------------------
# 3️⃣1️⃣ Make the virtual‑env visible to the runtime
# ------------------------------------------------------------------
ENV VIRTUAL_ENV=/usr/app/.venv \
    PATH="/usr/app/.venv/bin:${PATH}"

# ------------------------------------------------------------------
# 3️⃣2️⃣ Optional: expose the branch name and Kedro env at runtime
# ------------------------------------------------------------------
ENV BRANCH="main"
ENV KEDRO_ENV="prod"

# ------------------------------------------------------------------
# 3️⃣3️⃣ Copy the source tree (respect .dockerignore) and the
#       virtual‑env that was built in the previous stage.
# ------------------------------------------------------------------
COPY . /usr/app/
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# ------------------------------------------------------------------
# 3️⃣4️⃣ Git safety – tell git the directory is trusted (useful when
#       the container runs `git` commands later).
# ------------------------------------------------------------------
RUN git config --global --add safe.directory /usr/app

# ------------------------------------------------------------------
# 3️⃣5️⃣ Install the *application* itself (no dev deps, no editable mode)
# ------------------------------------------------------------------
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# ------------------------------------------------------------------
# 3️⃣6️⃣ Drop privileges – run everything as the non‑root user we created.
# ------------------------------------------------------------------
USER kedro_user
