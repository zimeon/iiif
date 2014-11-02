from test import BaseTest

class Test_Quality_Color(BaseTest):
    label = 'Color quality'
    level = 2
    category = 5
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            params = {'quality': 'color'}
            img = result.get_image(params)
            self.validationInfo.check('quality', img.mode, 'RGB', result)
            return result
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            raise