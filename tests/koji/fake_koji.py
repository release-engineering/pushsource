class FakeKojiController(object):
    def __init__(self):
        self.rpm_data = {}
        self.build_data = {}
        self.last_url = None

    def session(self, url):
        self.last_url = url
        return FakeKojiSession(self)


class FakeKojiSession(object):
    def __init__(self, controller):
        self._ctrl = controller

    def getRPM(self, rpm):
        return self._ctrl.rpm_data.get(rpm)

    def getBuild(self, build_id):
        return self._ctrl.build_data.get(build_id)
