from test import BaseTest, ValidatorError
import random

class Test_Rot_Region_Basic(BaseTest):
    label = 'Rotation of region by 90 degree values'
    level = {u'2.0': 2, u'1.0': 1, u'1.1': 1}
    category = 4
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            s = 76
            # ask for a random region, at a random size < 100
            for i in range(4):
                x = random.randint(0,9)
                y = random.randint(0,9)
                # XXX should do non 180
                params = {'rotation': '180'}
                params['region'] = '%s,%s,%s,%s' % (x*100+13, y*100+13,s,s)
                img = result.get_image(params)
                if not img.size[0] in [s-1, s, s+1]:   # allow some leeway for rotation
                    raise ValidatorError('size', img.size, (s,s))        
                ok = self.validationInfo.do_test_square(img,x,y, result)
                if not ok:
                    raise ValidatorError('color', 1, self.validationInfo.colorInfo[0][0], result)            
            return result
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            raise