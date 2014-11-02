from test import BaseTest, ValidatorError

class Test_Linkheader_Canonical(BaseTest):
    label = 'Canonical Link Header'
    level = 3
    category = 7
    versions = [u'2.0']
    validationInfo = None

    def run(self, result):

        url = result.make_url(params={})
        data = result.fetch(url)
        try:
            lh = result.last_headers['link']
        except KeyError:
            raise ValidatorError('canonical', '', 'URI', result)
        links = result.parse_links(lh)
        canonical = result.get_uri_for_rel(links, 'canonical')
        if not canonical:
            raise ValidatorError('canonical', '', 'URI', result)
        else:
            result.tests.append('linkheader')
            return result