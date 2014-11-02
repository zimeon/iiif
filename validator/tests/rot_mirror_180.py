from test import BaseTest, ValidatorError

class Test_Rot_Mirror_180(BaseTest):
    label = 'Mirroring plus 180 rotation'
    level = 3
    category = 4
    versions = [u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            params = {'rotation': '!180'}
            img = result.get_image(params)
            s = 1000
            if not img.size[0] in [s-1, s, s+1]:
                raise ValidatorError('size', img.size, (s,s))  

            #0,0 vs 9,9
            box = (12,12,76,76)
            sqr = img.crop(box)
            ok = self.validationInfo.do_test_square(sqr, 0, 9, result)
            if not ok:
                raise ValidatorError('mirror', 1, self.validationInfo.colorInfo[9][9], result)

            # 9,9 vs 0,0
            box = (912,912,976,976)
            sqr = img.crop(box)
            ok = self.validationInfo.do_test_square(sqr, 9, 0, result)
            if not ok:
                raise ValidatorError('mirror', 1, self.validationInfo.colorInfo[0][0], result)             
            return result             
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            raise