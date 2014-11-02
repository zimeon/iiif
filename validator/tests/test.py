
class BaseTest(object):
    label = "test name"
    level = 0
    category = 0
    versions = []
    validationInfo = None

    def __init__(self, info):
        self.validationInfo = info

    @classmethod
    def make_info(cls, version):
    	if version and not version in cls.versions:
			return {}            
        data = {'label': cls.label, 'level':cls.level, 'versions': cls.versions, 'category': cls.category}
        if type(cls.level) == dict:
            # If not version, need to make a choice... make it max()
            if version:
                data['level'] = cls.level[version]
            else:
                data['level'] = max(cls.level.values())
        return data

class ValidatorError(Exception):
    def __init__(self, type, got, expected, result=None):
        self.type = type
        self.got = got
        self.expected = expected
        if result != None:
            self.url = result.last_url
            self.headers = result.last_headers
            self.status = result.last_status
        else:
            self.url = None
            self.headers = None
            self.status = None
                
    def __str__(self):
        return "Expected %r for %s; Got: %r" % (self.expected, self.type, self.got)



        