from rest_framework.renderers import JSONRenderer
from rest_framework.utils.serializer_helpers import ReturnDict


class CustomJSONRenderer(JSONRenderer):

    def render(self, data, accepted_media_type=None, renderer_context=None):
       

        response_dict = {
            'status': True,
            'message': 'Successful',
            'data': data
        }
        response = renderer_context['response']

        if response.status_code >= 200 and response.status_code <= 299:
            response_dict['status'] = True
        else:
            response_dict['status'] = False
        
            if data and data.get('data'):
                data = data.get("data")
            try:
                errors = [data[k][0] for k in data]
                response_dict['message'] =list(data.keys())[0] + " - " + errors[0] 
            except Exception:
                response_dict['message'] = 'Unsuccessful'
        if type(data) in (ReturnDict, dict):

            if data.get('data') is not None:
                response_dict['data'] = data.get('data')
            else:
                response_dict['data'] = data

            if data.get('status') == False:
                response_dict['status'] = False

            # elif data.get('status'):
            #     response_dict['status'] = data.get('status')
            #     data.pop('status')

            # if data.get('status') in ['failure', False]:
            #
            #     if data.get('error_data'):
            #         response_dict['error_data'] = data.get('error_data')
            #     else:
            #         response_dict['error_data'] = {}
            #     if data.get('error_message'):
            #         response_dict['error_message'] = data.get('error_message')
            #     else:
            #         response_dict['error_message'] = ""

            if data.get('message'):
                response_dict['message'] = data.get('message')
                data.pop('message')
            elif data.get('detail'):
                response_dict['message'] = data.get('detail')
                data.pop('detail')

        data = response_dict
        return super().render(data, accepted_media_type, renderer_context)
