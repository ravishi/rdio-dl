from requests_oauthlib import OAuth1Session


class RdioOAuth1Session(OAuth1Session):

    api_url = u'http://api.rdio.com/1/'
    access_token_url = u'http://api.rdio.com/oauth/access_token'
    request_token_url = u'http://api.rdio.com/oauth/request_token'

    def fetch_request_token(self):
        return super(RdioOAuth1Session, self)\
                .fetch_request_token(self.request_token_url)

    def fetch_access_token(self):
        return super(RdioOAuth1Session, self)\
                .fetch_access_token(self.access_token_url)

    def set_authorization_pin(self, verifier):
        self._client.client.verifier = verifier

    def request(self, *args, **kwargs):
        # XXX For some unknown reason Rdio occasionally says our nonce is
        # duplicated. But if we keep trying it'll eventually work. So we
        # keep trying again until it works.

        retries = kwargs.pop('_duplicate_nonce_retries', 0)

        resp = super(RdioOAuth1Session, self).request(*args, **kwargs)

        if (resp.request.method == 'POST' and resp.status_code == 401
            and u'duplicate nonce' in resp.text.lower()):

            # retrying forever would be dumb
            if retries > 2:
                return resp

            intercepted_kwargs = {
                'data': kwargs.get('data'),
                'params': kwargs.get('params'),
            }

            return self.post(resp.request.url,
                             _duplicate_nonce_retries=(retries + 1),
                             **intercepted_kwargs)

        return resp

    def api_post(self, method, params=None):
        params = dict(params) if params else dict()
        params['method'] = method
        return self.post(self.api_url, data=params)
