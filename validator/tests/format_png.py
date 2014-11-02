from test import BaseTest

class Test_Format_Png(BaseTest):
    label = 'PNG format'
    level = 2
    category = 6
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            params = {'format': 'png'}
            img = result.get_image(params)
            self.validationInfo.check('quality', img.format, 'PNG', result)
            return result
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            raise