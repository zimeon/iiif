from test import BaseTest
import random

class Test_Rot_Full_Non90(BaseTest):
    label = 'Rotation by non 90 degree values'
    level = 3
    category = 4
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            r = random.randint(1,359)
            params = {'rotation': '%s' % r}
            img = result.get_image(params)
            # not sure how to test, other than we got an image       
            return result            
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            raise