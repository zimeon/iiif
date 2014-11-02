from test import BaseTest
import random

class Test_Rot_Region_Non90(BaseTest):
    label = 'Rotation by non 90 degree values'
    level = 3
    category = 4
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            # ask for a random region, at a random size < 100
            for i in range(4):
                r = random.randint(1,359)
                x = random.randint(0,9)
                y = random.randint(0,9)
                params = {'rotation': '%s'%r}
                params['region'] = '%s,%s,100,100' % (x*100, y*100)
                img = result.get_image(params)
                # not sure how to test
            return result
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            raise