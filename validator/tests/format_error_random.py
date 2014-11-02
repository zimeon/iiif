from test import BaseTest

class Test_Format_Error_Random(BaseTest):
    label = 'Random format gives 400'
    level = 1
    category = 6
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            url = result.make_url({'format': self.validationInfo.make_randomstring(3)})
            error = result.fetch(url)
            self.validationInfo.check('status', result.last_status, [400, 415, 503], result)
            return result
        except:
            raise