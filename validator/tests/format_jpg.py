from test import BaseTest

class Test_Format_Jpg(BaseTest):
    label = 'JPG format'
    level = {u'2.0': 0, u'1.0': 1, u'1.1': 1}
    category = 6
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            params = {'format': 'jpg'}
            img = result.get_image(params)
            self.validationInfo.check('quality', img.format, 'JPEG', result)
            return result
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            raise