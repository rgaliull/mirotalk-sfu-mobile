# MiroTalk SFU mobile profile

Reproducible custom image for MiroTalk SFU. The image is built from a pinned
upstream base and applies small source patches during the Docker build. This
repository contains no credentials, private domains, company names, room IDs,
user names, or server addresses.

## Included patches

- Force H.264 webcam negotiation and pass the selected codec correctly to
  `mediasoup-client`.
- Mobile capture profile: 640×360, 10 fps, one simulcast layer, 700 kbit/s.
- Desktop capture profile: 15 fps, two simulcast layers, 350/1200 kbit/s.
- Mobile receivers use the full-resolution remote layer while limiting the
  temporal layer to reduce decode work.
- Bridge a verified OIDC session into a short-lived presenter token for
  Socket.IO joins.
- Guest lobby with approval by an authenticated presenter.
- Replay pending lobby requests when a presenter joins later.
- Retry camera publication after a guest is approved.
- Optional duplicate display names for multiple devices.
- Privacy-safe video telemetry containing only codec/profile/encodings.
- Virtual Background grid initialization when its settings tab is opened.

## Runtime environment

```yaml
ROOM_LOBBY: "true"
PRESENTER_JOIN_FIRST: "false"
ALLOW_DUPLICATE_PEER_NAMES: "true"
```

Keep the deployment's existing OIDC variables, network mode, UDP media port
range, and worker placement. Do not enable `PRESENTER_JOIN_FIRST`: the first
guest in an empty room would otherwise become presenter.

## Build and publish

Configure repository secrets `GHCR_USERNAME` and `GHCR_TOKEN`; the latter must
have package write permission. The workflow publishes a version tag and an
immutable commit tag to the repository owner's GHCR namespace.

```bash
docker buildx build --platform linux/amd64 \
  --file Dockerfile.mobile \
  --tag ghcr.io/<owner>/mirotalk-sfu-mobile:<version> \
  --push .
```

Make the container package public if Swarm nodes pull it without registry
credentials. Use an immutable digest in the deployment UI, not a mutable tag.

## Deployment and verification

Replace only the MiroTalk service image in the deployment UI and update the
stack. Force-reload browser clients after an image update because JavaScript
assets can be cached.

Verify that:

1. An authenticated OIDC user can join from multiple devices with the same
   display name.
2. Guests entering before or after the presenter appear in the presenter
   lobby.
3. Approving a guest starts that guest's audio/video producer.
4. WebRTC stats show H.264; mobile sends one encoding near 700 kbit/s and
   desktop sends two near 350/1200 kbit/s.
5. Media uses UDP whenever the client network permits it.

An active-room listing endpoint may be protected by the deployment's OIDC
middleware and redirect unauthenticated requests to the identity provider.

## Rollback

Restore the previous pinned upstream image and update the stack. No database
migration is involved; all patches exist only inside the built image.
