#!/usr/bin/env python3.6
"""Make application to group all commands related to the container: build, run, tests and some external utilities.
"""
import os
import shlex
import sys

try:
    from clinner.command import command, Type as CommandType
    from clinner.run import Main as BaseMain
except ImportError:
    import imp
    import pip
    import site

    print('Installing Clinner')
    pip.main(['install', '--user', '-qq', 'clinner'])

    imp.reload(site)

    from clinner.command import command, Type as CommandType
    from clinner.run import Main as BaseMain

# Constants
DOCKER_IMAGE = 'knockout-assignment'
DOCKERFILE = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'Dockerfile')
DEFAULT_APP = 'app'


# Commands
@command(command_type=CommandType.SHELL_WITH_HELP,
         args=((('--name',), {'help': 'Docker image name', 'default': DOCKER_IMAGE}),
               (('--tag',), {'help': 'Docker image tag', 'default': 'latest'}),
               (('--dockerfile',), {'help': 'Dockefile path', 'default': DOCKERFILE}),),
         parser_opts={'help': 'Build docker image'})
def build(*args, **kwargs):
    tag = f'{kwargs["name"]}:{kwargs["tag"]}'
    return [shlex.split(f'docker build -f {kwargs["dockerfile"]} -t {tag} .')] + list(args)


@command(command_type=CommandType.SHELL_WITH_HELP, parser_opts={'help': 'Up application stack'})
def up(*args, **kwargs):
    return [shlex.split('docker-compose up -d')]


@command(command_type=CommandType.SHELL_WITH_HELP, parser_opts={'help': 'Down application stack'})
def down(*args, **kwargs):
    return [shlex.split('docker-compose down')]


@command(command_type=CommandType.SHELL_WITH_HELP, parser_opts={'help': 'Restart application stack'})
def restart(*args, **kwargs):
    return down() + up()


@command(command_type=CommandType.SHELL, parser_opts={'help': 'Run application'})
def run(*args, **kwargs):
    return [shlex.split(f'docker-compose run {DEFAULT_APP}') + list(args)]


@command(command_type=CommandType.SHELL_WITH_HELP,
         args=((('--format',), {'default': 'text', 'help': 'Output format'}),),
         parser_opts={'help': 'Run unit tests'})
def prospector(*args, **kwargs):
    return [shlex.split(f'docker-compose run {DEFAULT_APP} --quiet prospector --output-format={kwargs["format"]}')]


@command(command_type=CommandType.SHELL_WITH_HELP, parser_opts={'help': 'Run unit tests'})
def unit_tests(*args, **kwargs):
    return [shlex.split(f'docker-compose run {DEFAULT_APP} unit_tests') + list(args)]


@command(command_type=CommandType.SHELL_WITH_HELP, parser_opts={'help': 'Run acceptance tests'},
         args=((('-c', '--clean'), {'action': 'store_true', 'help': 'Clean up all containers after running'}),
               (('--build',), {'action': 'store_true', 'help': 'Build acceptance tests runner image'}),),)
def acceptance_tests(*args, **kwargs):
    if kwargs['build']:
        # Build test runner image
        cmds = [shlex.split('docker build -f tests/acceptance/Dockerfile -t knockout-assignment-acceptance:latest '
                            'tests/acceptance')]
    else:
        # Run tests
        cmds = [shlex.split('docker-compose -f tests/acceptance/docker-compose-acceptance.yml run '
                            '--rm test acceptance_tests') + list(args)]

        if kwargs['clean']:
            cmds += [shlex.split('docker-compose -f tests/acceptance/docker-compose-acceptance.yml '
                                 'down -v --remove-orphans')]

    return cmds


# Main
class Main(BaseMain):
    commands = (
        'build',
        'up',
        'down',
        'restart',
        'run',
        'prospector',
        'unit_tests',
        'acceptance_tests',
    )


if __name__ == '__main__':
    sys.exit(Main().run())
