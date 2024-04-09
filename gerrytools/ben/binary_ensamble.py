import docker
from pathlib import Path
from typing import Optional
import os
from .docker_manager import managed_docker_container
import logging

logger = logging.getLogger("ben")


def ben(
    mode: str,
    input_file_path: str,
    output_file_path: Optional[str] = None,
    verbose: bool = True,
    docker_image_name: str = "mgggdev/replicate:v0.2",
    docker_client_args: Optional[dict] = None,
):
    """
    Runs the BEN cli tool from the `binary-ensamble <https://crates.io/crates/binary-ensemble>`_
    crate in a Docker container. By convention, the output file will be written to the same
    directory as the input file and any duplicates will be overwritten.

    Args:
        mode (str): The mode to run the program in. Must be one of 'encode', 'x-encode', 'decode', 'x-decode', 'xz-encode', 'xz-decode'.
        input_file_path (str): The path to the input file to read from.
        output_file_name (str, optional): The name of the output file to write to.
            When not given, the output name will be derived from the input name
            according to a set of heuristics (usually adding or deleting "ben" or "xben"
            in the file extension). Defaults to None.
        verbose (bool, optional): Whether to run the program in verbose mode. Defaults to True.
        docker_image_name (str, optional): The name of the Docker image to run the program in.
            Defaults to "mgggdev/replicate:v0.2".
        docker_client_args (dict, optional): Additional arguments to pass to the Docker client.
            Used primarily if there are multiple docker contexts on the same machine.
            Defaults to None.
    """

    if docker_client_args is not None:
        client = docker.DockerClient(**docker_client_args)
    else:
        client = docker.from_env()

    # Set up the input and output paths
    input_parent_path = Path(input_file_path).parent
    input_file_name = Path(input_file_path).name

    if output_file_path is not None:
        output_parent_path = Path(output_file_path).parent
        output_file_name = Path(output_file_path).name
    else:
        output_parent_path = input_parent_path
        output_file_name = None

    os.makedirs(output_parent_path, exist_ok=True)

    config_args = {
        "name": "ben_runner",
        "image": docker_image_name,
        "detach": True,
        "auto_remove": True,
        "tty": True,
        "stdin_open": True,
    }

    if input_parent_path == output_parent_path:
        config_args["volumes"] = {
            os.getcwd(): {"bind": "/home/ben/working", "mode": "rw"},
            input_parent_path.resolve(): {
                "bind": "/home/ben/io",
                "mode": "rw",
            },
        }
        docker_input_path = "/home/ben/io"
        docker_output_path = "/home/ben/io"
    else:
        config_args["volumes"] = {
            os.getcwd(): {"bind": "/home/ben/working", "mode": "rw"},
            input_parent_path.resolve(): {
                "bind": "/home/ben/input",
                "mode": "rw",
            },
            output_parent_path.resolve(): {
                "bind": "/home/ben/output",
                "mode": "rw",
            },
        }
        docker_input_path = "/home/ben/input"
        docker_output_path = "/home/ben/output"

    with managed_docker_container(client, config_args) as container:
        # Pull the docker image and set up the container
        try:
            print(f"Pulling Docker image {config_args['image']}")
            client.images.pull(config_args["image"])
        except Exception as e:
            print(
                f"Error comparing docker container {config_args['image']} against web version. "
                f"Attempting to run using local image"
            )

        # Build the command to run in the container
        if mode not in [
            "encode",
            "x-encode",
            "decode",
            "x-decode",
            "xz-compress",
            "xz-decompress",
        ]:
            print(
                f"Invalid mode: {mode}. "
                "Mode must be one of 'encode', 'x-encode', 'decode', 'x-decode', 'xz-compress', "
                "'xz-decompress'"
            )
            return

        ben_cmd = f"ben {docker_input_path}/{input_file_name} -w -m {mode}"

        if verbose:
            ben_cmd += " -v"

        if output_file_name is not None:
            ben_cmd += f" -o {docker_output_path}/{Path(output_file_name).name}"

        cmd = ["sh", "-c", f"{ben_cmd}"]

        logger.debug(f"Running command: {cmd}")
        exec_id = client.api.exec_create(
            container.id, cmd=cmd, tty=False, stdout=True, stderr=True, stdin=False
        )

        output_generator = client.api.exec_start(
            exec_id=exec_id, stream=True, detach=False
        )

        for output in output_generator:
            print(output.decode("utf-8"), end="")

    client.close()
