from odoo.http import JsonRPCDispatcher


class JsonRPCDispatcherInherit(JsonRPCDispatcher):

    def _response(self, result=None, error=None):
        res = super(JsonRPCDispatcherInherit, self)._response(result, error)
        if self.request.context.get("remove_jsonrpc", False):
            response = {}
            if error is not None:
                response['error'] = error
            if result is not None:
                response = result
            status = 200
            if result.get("status"):
                status = result.get("status")
                result.pop("status")
            return self.request.make_json_response(response, status=status)
        return res
