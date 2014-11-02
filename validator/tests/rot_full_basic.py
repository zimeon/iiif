from test import BaseTest, ValidatorError

class Test_Rot_Full_Basic(BaseTest):
    label = 'Rotation by 90 degree values'
    level = {u'2.0': 2, u'1.0': 1, u'1.1': 1}
    category = 4
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            params = {'rotation': '180'}
            img = result.get_image(params)
            s = 1000
            if not img.size[0] in [s-1, s, s+1]:
                raise ValidatorError('size', img.size, (s,s))  
            # Test 0,0 vs 9,9
            box = (12,12,76,76)
            sqr = img.crop(box)
            ok = self.validationInfo.do_test_square(sqr, 9, 9, result)
            if not ok:
                raise ValidatorError('color', 1, self.validationInfo.colorInfo[9][9], result)
            box = (912,912,976,976)
            sqr = img.crop(box)
            ok = self.validationInfo.do_test_square(sqr, 0, 0, result)
            if not ok:
                raise ValidatorError('color', 1, self.validationInfo.colorInfo[0][0], result)

            params = {'rotation': '90'}
            img = result.get_image(params)
            s = 1000
            if not img.size[0] in [s-1, s, s+1]:
                raise ValidatorError('size', img.size, (s,s))  
            # Test 0,0 vs 9,0
            box = (12,12,76,76)
            sqr = img.crop(box)
            ok = self.validationInfo.do_test_square(sqr, 0, 9, result)
            if not ok:
                raise ValidatorError('color', 1, self.validationInfo.colorInfo[9][9], result)
            box = (912,912,976,976)
            sqr = img.crop(box)
            ok = self.validationInfo.do_test_square(sqr, 9, 0, result)
            if not ok:
                raise ValidatorError('color', 1, self.validationInfo.colorInfo[0][0], result)

            params = {'rotation': '270'}
            img = result.get_image(params)
            s = 1000
            if not img.size[0] in [s-1, s, s+1]:
                raise ValidatorError('size', img.size, (s,s))  
            # Test 0,0 vs 9,0
            box = (12,12,76,76)
            sqr = img.crop(box)
            ok = self.validationInfo.do_test_square(sqr, 9, 0, result)
            if not ok:
                raise ValidatorError('color', 1, self.validationInfo.colorInfo[9][9], result)
            box = (912,912,976,976)
            sqr = img.crop(box)
            ok = self.validationInfo.do_test_square(sqr, 0, 9, result)
            if not ok:
                raise ValidatorError('color', 1, self.validationInfo.colorInfo[0][0], result)

            return result 

        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            raise