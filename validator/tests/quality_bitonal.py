from test import BaseTest

class Test_Quality_Bitonal(BaseTest):
    label = 'Bitonal quality'
    level = 2
    category = 5
    versions = [u'1.0', u'1.1', u'2.0']
    validationInfo = None

    def run(self, result):
        try:
            params = {'quality': 'bitonal', 'format':'png'}
            img = result.get_image(params)

            cols = img.getcolors()
            # cols should be [(x, 0), (y,255)] or [(x,(0,0,0)), (y,(255,255,255))]
            if img.mode == '1' or img.mode == 'L':
                return self.validationInfo.check('quality', 1, 1, result)
            else:
                # check vast majority of px are 0,0,0 or 255,255,255
                okpx = sum([x[0] for x in cols if sum(x[1]) < 15 or sum(x[1]) > 750])
                if okpx > 650000:
                    return self.validationInfo.check('quality', 1,1, result)
                else:
                    return self.validationInfo.check('quality', 1,0, result)
        except:
            self.validationInfo.check('status', result.last_status, 200, result)
            raise