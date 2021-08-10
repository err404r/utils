#!/usr/bin/env python3

from argparse import ArgumentParser
from sys import exit
# IMPORTANT to use docker over ssh paramiko must be installed
import docker

CHECK_OK = 0
CHECK_WARNING = 1
CHECK_CRITICAL = 2
CHECK_UNKNOWN = 3


def check_exit(exitcode, msg):
    print(msg)
    exit(exitcode)


def parse_arguments():
    arg_parser = ArgumentParser(
        description="Docker health check with optional restart")
    arg_parser.add_argument(
        "--url",
        dest="url",
        required=True,
        help="url for connecting to docker server"
    )
    arg_parser.add_argument(
        "--name",
        dest="name",
        required=True,
        help="name of the container to check"
    )
    arg_parser.add_argument(
        "--min-streak",
        dest="min_streak",
        type=int,
        default=0,
        help="minimal amount of consequency failed healthchecks "
             "to mark service as failed"
    )
    arg_parser.add_argument(
        "--restart",
        dest="restart",
        type=int,
        choices=[0, 1],
        default=0,
        help="if 1 try to restart container if it is unhealthy"
    )
    arg_parser.add_argument(
        "--timeout",
        dest="timeout",
        type=int,
        default=5,
        help="restart timeout"
    )
    arg_parser.add_argument(
        "--last-state",
        dest="last_state",
        type=int,
        default=CHECK_UNKNOWN,
        help="state of the previous run, use with restart"
    )

    return arg_parser.parse_args()


def process_failure(container, cmd_args):
    if cmd_args.restart and cmd_args.last_state == CHECK_OK:
        container.restart(timeout=cmd_args.timeout)
        check_exit(
            CHECK_WARNING,
            f"service {cmd_args.name} is unhealthy, "
            "container has been restarted"
        )
    else:
        check_exit(
            CHECK_CRITICAL,
            f"service {cmd_args.name} is unhealthy"
        )


def check_health_status(cmd_args):
    client = docker.DockerClient(base_url=cmd_args.url)
    service_containers = client.containers.list(
        filters={"name": cmd_args.name}
    )
    if len(service_containers) == 0:
        check_exit(
            CHECK_CRITICAL,
            f"container {cmd_args.name} is not running"
        )
    for container in service_containers:
        health_info = container.attrs['State']['Health']
        if health_info['FailingStreak'] > cmd_args.min_streak:
            process_failure(container, cmd_args)
        else:
            check_exit(
                CHECK_OK,
                f"service {cmd_args.name} is healthy"
            )


if __name__ == "__main__":
    cmd_args = parse_arguments()
    check_health_status(cmd_args)
