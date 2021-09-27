import logging
import json
from six.moves import shlex_quote

from . import Executor, ContainerExecutorImpl


LOG = logging.getLogger("pubtools.quay")


class SkopeoCommands(object):
    """
    Set of skopeo commands ran on executor.
    """

    def __init__(self, executor):
        self.executor = executor

    def tag_images(self, source_ref, dest_refs, all_arch=False):
        """
        Copy image from source to destination(s) using skopeo.

        Args:
            source_ref (str):
                Reference of the source image.
            dest_refs ([str]):
                List of target references to copy the image to.
            all_arch (bool):
                Whether to copy all architectures (if multiarch image)
        """
        if all_arch:
            cmd = "skopeo copy --all docker://{0} docker://{1}"
        else:
            cmd = "skopeo copy docker://{0} docker://{1}"

        for dest_ref in dest_refs:
            LOG.info("Tagging source '%s' to destination '%s'", source_ref, dest_ref)
            self.executor._run_cmd(
                cmd.format(shlex_quote(source_ref), shlex_quote(dest_ref))
            )
            LOG.info("Destination image %s has been tagged.", dest_ref)

        LOG.info("Tagging complete.")

    def skopeo_login(self, username=None, password=None):
        """
        Attempt to login to Quay if no login credentials are present.

        This method is reimplemented because it uses a different approach to input the password.

        Args:
            username (str):
                Username for login.
            password (str):
                Password for login.
        """
        cmd_check = "skopeo login --get-login quay.io"
        out, err = self.executor._run_cmd(cmd_check, tolerate_err=True)
        if username and username in out:
            LOG.info("Already logged in to Quay.io")
            return

        if not username or not password:
            raise ValueError(
                "Skopeo login credentials are not present. Quay user and token must be provided."
            )
        LOG.info("Logging in to Quay with provided credentials")

        password_file = "skopeo_password.txt"
        self.executor._add_file(password, password_file)

        cmd_login = (
            " sh -c 'cat /tmp/{1} | skopeo login --authfile $HOME/.docker/config.json"
            " -u {0} --password-stdin quay.io'"
        ).format(shlex_quote(username), shlex_quote(password_file))
        out, err = self.executor._run_cmd(cmd_login)

        if "Login Succeeded" in out:
            LOG.info("Login successful")
        else:
            raise RuntimeError(
                "Login command didn't generate expected output. "
                "STDOUT: '{0}', STDERR: '{1}'".format(out, err)
            )

    def skopeo_inspect(self, image_ref, raw=False):
        """
        Run skopeo inspect and return the result.

        NOTE: inspect command will not be run with the --raw argument. This option only returns an
        image manifest, which can be gathered by QuayClient. 'raw' argument in this function
        denotes if the result should be parsed or returned raw.

        Args:
            image_ref (str):
                Image reference to inspect.
            raw (bool):
                Whether to parse the returned JSON, or return raw.
        Returns (dict|str):
            Result of skopeo inspect.
        """
        cmd = "skopeo inspect docker://{0}".format(image_ref)
        out, _ = self.executor._run_cmd(cmd)

        if raw:
            return out
        return json.loads(out)


class SkopeoContainerExecutor(Executor):
    executor_cls = ContainerExecutorImpl
    commands_cls = SkopeoCommands
