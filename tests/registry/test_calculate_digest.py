import json

import pytest

from pushsource._impl.utils.containers.request import _calculate_digest

# curl -H 'Accept: application/vnd.docker.distribution.manifest.list.v2+json' -Ls \
#   https://registry.access.redhat.com/v2/ubi8/ubi/manifests/sha256:910f6bc0b5ae9b555eb91b88d28d568099b060088616eba2867b07ab6ea457c7
UBI8_LIST = b"""{
    "manifests": [
        {
            "digest": "sha256:5e334d76fc059f7b44ee8fc2da6a2e8b240582d0214364c8c88596d20b33d7f1",
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "platform": {
                "architecture": "amd64",
                "os": "linux"
            },
            "size": 737
        },
        {
            "digest": "sha256:043094708e3456291bebce04aa3f8992ad394f05d654ca438557890c45dc93b3",
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "platform": {
                "architecture": "arm64",
                "os": "linux"
            },
            "size": 737
        },
        {
            "digest": "sha256:0cc5439e49d455d249746f671f682ae92acd6b497f7fda0e1fbf0b4e5bde9034",
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "platform": {
                "architecture": "ppc64le",
                "os": "linux"
            },
            "size": 737
        },
        {
            "digest": "sha256:9abac60525cb239de3b773d2b46536618bc9b81fa43d85fcbe3b0deaa34876e1",
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "platform": {
                "architecture": "s390x",
                "os": "linux"
            },
            "size": 737
        }
    ],
    "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
    "schemaVersion": 2
}"""


# curl -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' -Ls \
#   https://registry.access.redhat.com/v2/ubi8/ubi/manifests/sha256:9abac60525cb239de3b773d2b46536618bc9b81fa43d85fcbe3b0deaa34876e1
UBI8_IMAGE2 = b"""{
   "schemaVersion": 2,
   "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
   "config": {
      "mediaType": "application/vnd.docker.container.image.v1+json",
      "size": 4362,
      "digest": "sha256:cf6c26ba556854c8d3ed6bf8d40f140b77ce6a857aa7003407b1d0eac1d31e87"
   },
   "layers": [
      {
         "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
         "size": 80581963,
         "digest": "sha256:8ad8514f24ae2d12ab325ad5ffb76870040fc996dde80c0b0d54f663045d8932"
      },
      {
         "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
         "size": 1784,
         "digest": "sha256:53ae128587a66ae4816f2dc2df684d892b1a79f0dda7e5d49ed1fcb445857926"
      }
   ]
}"""

# curl -H 'Accept: application/vnd.docker.distribution.manifest.v1+json' -Ls \
#   https://registry.access.redhat.com/v2/ubi8/ubi/manifests/sha256:c044fec0c91dc1d0b2855324fbd3715cb958200c27bc5250f9dbc71466ad25b9
UBI8_IMAGE1 = b"""{
   "schemaVersion": 1,
   "name": "ubi8/ubi",
   "tag": "latest",
   "architecture": "amd64",
   "fsLayers": [
      {
         "blobSum": "sha256:63f9f4c31162a6a5dacd999a0dc65007e15b2ca6b2d9360a1234c27de12e7f38"
      },
      {
         "blobSum": "sha256:ce3c6836540f978b55c511d236429e26b7a45f5a6f1204ab8d4378afaf77332f"
      }
   ],
   "history": [
      {
         "v1Compatibility": "{\\"architecture\\":\\"amd64\\",\\"config\\":{\\"Hostname\\":\\"b20a3e8238f9\\",\\"Domainname\\":\\"\\",\\"User\\":\\"\\",\\"AttachStdin\\":false,\\"AttachStdout\\":false,\\"AttachStderr\\":false,\\"Tty\\":false,\\"OpenStdin\\":false,\\"StdinOnce\\":false,\\"Env\\":[\\"PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\\",\\"container=oci\\"],\\"Cmd\\":[\\"/bin/bash\\"],\\"ArgsEscaped\\":true,\\"Image\\":\\"6c0c06bb29436721ce6844efc80334a2dd87c939a4fdaf5de4f539bf0e910a3a\\",\\"Volumes\\":null,\\"WorkingDir\\":\\"\\",\\"Entrypoint\\":null,\\"OnBuild\\":[],\\"Labels\\":{\\"architecture\\":\\"x86_64\\",\\"build-date\\":\\"2021-11-03T13:57:13.897992\\",\\"com.redhat.build-host\\":\\"cpt-1006.osbs.prod.upshift.rdu2.redhat.com\\",\\"com.redhat.component\\":\\"ubi8-container\\",\\"com.redhat.license_terms\\":\\"https://www.redhat.com/en/about/red-hat-end-user-license-agreements#UBI\\",\\"description\\":\\"The Universal Base Image is designed and engineered to be the base layer for all of your containerized applications, middleware and utilities. This base image is freely redistributable, but Red Hat only supports Red Hat technologies through subscriptions for Red Hat products. This image is maintained by Red Hat and updated regularly.\\",\\"distribution-scope\\":\\"public\\",\\"io.k8s.description\\":\\"The Universal Base Image is designed and engineered to be the base layer for all of your containerized applications, middleware and utilities. This base image is freely redistributable, but Red Hat only supports Red Hat technologies through subscriptions for Red Hat products. This image is maintained by Red Hat and updated regularly.\\",\\"io.k8s.display-name\\":\\"Red Hat Universal Base Image 8\\",\\"io.openshift.expose-services\\":\\"\\",\\"io.openshift.tags\\":\\"base rhel8\\",\\"maintainer\\":\\"Red Hat, Inc.\\",\\"name\\":\\"ubi8\\",\\"release\\":\\"200\\",\\"summary\\":\\"Provides the latest release of Red Hat Universal Base Image 8.\\",\\"url\\":\\"https://access.redhat.com/containers/#/registry.access.redhat.com/ubi8/images/8.5-200\\",\\"vcs-ref\\":\\"3aadd00326f3dd6cfe65ee31017ab98915fddb56\\",\\"vcs-type\\":\\"git\\",\\"vendor\\":\\"Red Hat, Inc.\\",\\"version\\":\\"8.5\\"}},\\"container_config\\":{\\"Hostname\\":\\"b20a3e8238f9\\",\\"Domainname\\":\\"\\",\\"User\\":\\"\\",\\"AttachStdin\\":false,\\"AttachStdout\\":false,\\"AttachStderr\\":false,\\"Tty\\":false,\\"OpenStdin\\":false,\\"StdinOnce\\":false,\\"Env\\":[\\"PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\\",\\"container=oci\\"],\\"Cmd\\":[\\"/bin/sh\\",\\"-c\\",\\"mv -fZ /tmp/ubi.repo /etc/yum.repos.d/ubi.repo || :\\"],\\"ArgsEscaped\\":true,\\"Image\\":\\"sha256:3582abe7db5e8e0e9be5201c8212b1d894f65096c66cf61b9d582c1f4b3d747b\\",\\"Volumes\\":null,\\"WorkingDir\\":\\"\\",\\"Entrypoint\\":null,\\"OnBuild\\":[],\\"Labels\\":{\\"architecture\\":\\"x86_64\\",\\"build-date\\":\\"2021-11-03T13:57:13.897992\\",\\"com.redhat.build-host\\":\\"cpt-1006.osbs.prod.upshift.rdu2.redhat.com\\",\\"com.redhat.component\\":\\"ubi8-container\\",\\"com.redhat.license_terms\\":\\"https://www.redhat.com/en/about/red-hat-end-user-license-agreements#UBI\\",\\"description\\":\\"The Universal Base Image is designed and engineered to be the base layer for all of your containerized applications, middleware and utilities. This base image is freely redistributable, but Red Hat only supports Red Hat technologies through subscriptions for Red Hat products. This image is maintained by Red Hat and updated regularly.\\",\\"distribution-scope\\":\\"public\\",\\"io.k8s.description\\":\\"The Universal Base Image is designed and engineered to be the base layer for all of your containerized applications, middleware and utilities. This base image is freely redistributable, but Red Hat only supports Red Hat technologies through subscriptions for Red Hat products. This image is maintained by Red Hat and updated regularly.\\",\\"io.k8s.display-name\\":\\"Red Hat Universal Base Image 8\\",\\"io.openshift.expose-services\\":\\"\\",\\"io.openshift.tags\\":\\"base rhel8\\",\\"maintainer\\":\\"Red Hat, Inc.\\",\\"name\\":\\"ubi8\\",\\"release\\":\\"200\\",\\"summary\\":\\"Provides the latest release of Red Hat Universal Base Image 8.\\",\\"url\\":\\"https://access.redhat.com/containers/#/registry.access.redhat.com/ubi8/images/8.5-200\\",\\"vcs-ref\\":\\"3aadd00326f3dd6cfe65ee31017ab98915fddb56\\",\\"vcs-type\\":\\"git\\",\\"vendor\\":\\"Red Hat, Inc.\\",\\"version\\":\\"8.5\\"}},\\"created\\":\\"2021-11-03T13:57:53.878769Z\\",\\"docker_version\\":\\"1.13.1\\",\\"id\\":\\"382eb0ec0c9262cc52b1b6e4a6d7df84e1bfefe6c6f09ab2620aec076c35708a\\",\\"os\\":\\"linux\\",\\"parent\\":\\"55451e8753cc141f82cff6235d99a774e3b245425cc547486ce0f99c3c6cc110\\"}"
      },
      {
         "v1Compatibility": "{\\"id\\":\\"55451e8753cc141f82cff6235d99a774e3b245425cc547486ce0f99c3c6cc110\\",\\"comment\\":\\"Imported from -\\",\\"created\\":\\"2021-11-03T13:57:39.79709821Z\\",\\"container_config\\":{\\"Cmd\\":[\\"\\"]}}"
      }
   ],
   "signatures": [
      {
         "header": {
            "jwk": {
               "crv": "P-256",
               "kid": "EZQE:QY3W:LZ7M:DHUW:FLDW:TRLU:UF4G:6AL5:D5L2:X2PH:OJVN:FNLJ",
               "kty": "EC",
               "x": "-hPxNwGHwnllz6Um-U3RnukN4h3PH0sD3tscViZYf6U",
               "y": "qDNafrhP1eJNwUKOIqs7c2m7cNK_DTYIEgjR2c_EIXU"
            },
            "alg": "ES256"
         },
         "signature": "XBvUKyIcJgDxK-iKNBTjqp8aKc9avZOpH6Zj55NnTpF26c_qWc311x1mAafFH926hTsxXUgPaOQ01VhwImOvaw",
         "protected": "eyJmb3JtYXRMZW5ndGgiOjUxMjksImZvcm1hdFRhaWwiOiJDbjAiLCJ0aW1lIjoiMjAyMS0xMS0xMFQwNzowNjozN1oifQ"
      }
   ]
}"""


@pytest.mark.parametrize(
    "raw_manifest,expected_digest",
    [
        (
            UBI8_LIST,
            "sha256:910f6bc0b5ae9b555eb91b88d28d568099b060088616eba2867b07ab6ea457c7",
        ),
        (
            UBI8_IMAGE2,
            "sha256:9abac60525cb239de3b773d2b46536618bc9b81fa43d85fcbe3b0deaa34876e1",
        ),
        (
            UBI8_IMAGE1,
            "sha256:c044fec0c91dc1d0b2855324fbd3715cb958200c27bc5250f9dbc71466ad25b9",
        ),
    ],
    ids=["ubi8-list", "ubi8-image2", "ubi8-image1"],
)
def test_calculate_digest(raw_manifest, expected_digest):
    manifest = json.loads(raw_manifest)
    actual_digest = _calculate_digest(raw_manifest, manifest)
    assert actual_digest == expected_digest
