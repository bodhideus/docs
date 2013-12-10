import re


class Service(object):
    def __init__(self, name, client=None, links=[], **options):
        if not re.match('^[a-zA-Z0-9_]+$', name):
            raise ValueError('Invalid name: %s' % name)

        self.name = name
        self.client = client
        self.links = links or []
        self.options = options

    @property
    def containers(self):
        return [c for c in self.client.containers() if parse_name(get_container_name(c))[0] == self.name]

    def start(self):
        if len(self.containers) == 0:
            self.start_container()

    def stop(self):
        self.scale(0)

    def scale(self, num):
        while len(self.containers) < num:
            self.start_container()

        while len(self.containers) > num:
            self.stop_container()

    def start_container(self, **override_options):
        options = dict(self.options)
        options.update(override_options)
        number = self.next_container_number()
        name = make_name(self.name, number)
        container = self.client.create_container(name=name, **options)
        self.client.start(
            container['Id'],
            links=self._get_links(),
        )

    def stop_container(self):
        self.client.kill(self.containers[0]['Id'])

    def next_container_number(self):
        numbers = [parse_name(get_container_name(c))[1] for c in self.containers]

        if len(numbers) == 0:
            return 1
        else:
            return max(numbers) + 1

    def get_names(self):
        return [get_container_name(c) for c in self.containers]

    def inspect(self):
        return [self.client.inspect_container(c['Id']) for c in self.containers]

    def _get_links(self):
        links = {}
        for service in self.links:
            for name in service.get_names():
                links[name] = name
        return links



def make_name(prefix, number):
    return '%s_%s' % (prefix, number)


def parse_name(name):
    match = re.match('^(.+)_(\d+)$', name)

    if match is None:
        raise ValueError("Invalid name: %s" % name)

    (service_name, suffix) = match.groups()

    return (service_name, int(suffix))


def get_container_name(container):
    return container['Names'][0][1:]
