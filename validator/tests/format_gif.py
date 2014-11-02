from test import BaseTest

class Test_Format_Gif(BaseTest):
    label = 'GIF format'
    level = 3
    category = 6
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            params = {'format': 'gif'}
            img = result.get_image(params)
            self.validationInfo.check('quality', img.format, 'GIF', result)
            return result
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            raise