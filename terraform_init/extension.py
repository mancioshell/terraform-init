import logging
import os

from localstack import config
from localstack.extensions.api import Extension, http, aws
from localstack.packages import InstallTarget
from localstack.runtime.init import ScriptRunner
from localstack.utils.run import run

from .packages import terraform_package, tflocal_package

LOG = logging.getLogger(__name__)


class TerraformInit(Extension):
    name = "terraform-init"

    def on_extension_load(self):
        logging.getLogger("terraform_init").setLevel(
            logging.DEBUG if config.DEBUG else logging.INFO
        )

    def on_platform_start(self):
        print("MyExtension: localstack is starting")

    def on_platform_ready(self):
        print("MyExtension: localstack is running")

    def update_gateway_routes(self, router: http.Router[http.RouteHandler]):
        pass

    def update_request_handlers(self, handlers: aws.CompositeHandler):
        pass

    def update_response_handlers(self, handlers: aws.CompositeResponseHandler):
        pass


class TflocalScriptRunner(ScriptRunner):
    name = "tflocal"

    def load(self, *args, **kwargs):
        terraform_package.install()
        tflocal_package.install()

    def should_run(self, script_file: str) -> bool:
        if os.path.basename(script_file) == "main.tf":
            return True
        return False

    def run(self, path: str) -> None:
        # create path to find ``terraform`` and ``tflocal`` binaries
        # TODO: better way to define path
        tf_path = terraform_package.get_installed_dir()
        install_dir = tflocal_package.get_installer()._get_install_dir(
            InstallTarget.VAR_LIBS
        )
        tflocal_path = f"{install_dir}/bin"
        env_path = f"{tflocal_path}:{tf_path}:{os.getenv('PATH')}"

        LOG.info("Applying terraform project from file %s", path)
        # run tflocal
        workdir = os.path.dirname(path)
        LOG.debug("Initializing terraform provider in %s", workdir)
        run(
            ["tflocal", f"-chdir={workdir}", "init", "-input=false"],
            env_vars={"PATH": env_path},
        )
        LOG.debug("Applying terraform file %s", path)
        run(
            ["tflocal", f"-chdir={workdir}", "apply", "-auto-approve"],
            env_vars={"PATH": env_path},
        )
