from collections import Iterable
from collections import namedtuple

class DotDict(dict):
    """dot.notation access to dictionary attributes"""

    def __getattr__(self, attr):
        return self.get(attr)

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __dir__(self):
        return self.keys()

    # Cargo-cultishly copied from: https://github.com/spindlelabs/pyes/commit/d2076b385c38d6d00cebfe0df7b0d1ba8df934bc
    def __deepcopy__(self, memo):
        return DotDict([(copy.deepcopy(k, memo), copy.deepcopy(v, memo)) for k, v in self.items()])


#Inspiration : https://codereview.stackexchange.com/questions/81794/dictionary-with-restricted-keys
class LimitedDotDict(DotDict):
    """dot.notation access to dictionary attributes, with limited keys
    

    Note: this class is pretty useless on its own.
    You need to subclass it like so:

    class MyLimitedDotDict(LimitedDotDict):
        _allowed_keys = set([
            "x", "y", "z"
        ])

    """

    _allowed_keys = set()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self._allowed_keys:
                raise KeyError("(__init__) key: {!r} not in allowed keys: {!r}".format(
                    key,
                    self._allowed_keys
                ))
            self[key] = value

    def __setitem__(self, key, val):
        if key not in self._allowed_keys:
            raise KeyError("(__setitem__) key: {!r} not in allowed keys: {!r}".format(
                key,
                self._allowed_keys
            ))
        dict.__setitem__(self, key, val)

    def __setattr__(self, key, val):
        if key not in self._allowed_keys:
            raise KeyError("(__setitem__) key: {!r} not in allowed keys: {!r}".format(
                key,
                self._allowed_keys
            ))
        dict.__setitem__(self, key, val)

class Rendered(object):
    pass

# class RenderedContentBlock(Rendered):
#     def __init__(self, content_block_type, header=None, subheader=None, content=None, styling=None):
#         self.content_block_type = content_block_type
#         self.header = header
#         self.subheader = subheader
#         self.content = content
#         self.styling = styling

class RenderedContentBlock(LimitedDotDict):
    _allowed_keys = set([
        "content_block_type",
        "header",
        "subheader",
        "content",
        "graph",
        "styling",
    ])

class RenderedSection(Rendered):
    pass

class RenderedDocument(Rendered):
    pass

class RenderedContentBlockWrapper(LimitedDotDict):
    _allowed_keys = set([
        "content_block",
        "section_loop",
        "content_block_loop",
    ])


# class DomStylingInfo(object):
#     """Basically a struct type for:
#     {
#         "classes": ["root_foo"],
#         "styles": {"root": "bar"},
#         "attributes": {"root": "baz"},
#     }
#     """
#     pass


# class UnstyledStringTemplate(object):
#     """Basically a struct type for:
#     {
#         "template": "$var1 $var2 $var3",
#         "params": {
#             "var1": "aaa",
#             "var2": "bbb",
#             "var3": "ccc",
#         }
#     }
#     """
#     pass


# class StylableStringTemplate(object):
#     """Basically a struct type for:
#     {
#         "template": "$var1 $var2 $var3",
#         "params": {
#             "var1": "aaa",
#             "var2": "bbb",
#             "var3": "ccc",
#         },
#         "styling": {
#             **DomStylingInfo, #Styling for the whole templated string
#             "default" : DomStylingInfo, #Default styling for parameters
#             "params" : { #Styling overrides on an individual parameter basis
#                 "var1" : DomStylingInfo,
#                 "var2" : DomStylingInfo,
#             },
#         }
#     }
#     """

#     def __init__(self):
#         pass

#     def validate(self):
#         pass

#     @classmethod
#     def render_styling(cls, styling):
#         """Adds styling information suitable for an html tag

#         styling = {
#             "classes": ["alert", "alert-warning"],
#             "attributes": {
#                 "role": "alert",
#                 "data-toggle": "popover",
#             },
#             "styles" : {
#                 "padding" : "10px",
#                 "border-radius" : "2px",
#             }
#         }

#         returns a string similar to:
#         'class="alert alert-warning" role="alert" data-toggle="popover" style="padding: 10px; border-radius: 2px"'

#         (Note: `render_styling` makes no guarantees about)

#         "classes", "attributes" and "styles" are all optional parameters.
#         If they aren't present, they simply won't be rendered.

#         Other dictionary keys are also allowed and ignored.
#         This makes it possible for styling objects to be nested, so that different DOM elements

#         #NOTE: We should add some kind of type-checking to styling
#         """

#         class_list = styling.get("classes", None)
#         if class_list == None:
#             class_str = ""
#         else:
#             if type(class_list) == str:
#                 raise TypeError("classes must be a list, not a string.")
#             class_str = 'class="'+' '.join(class_list)+'" '

#         attribute_dict = styling.get("attributes", None)
#         if attribute_dict == None:
#             attribute_str = ""
#         else:
#             attribute_str = ""
#             for k, v in attribute_dict.items():
#                 attribute_str += k+'="'+v+'" '

#         style_dict = styling.get("styles", None)
#         if style_dict == None:
#             style_str = ""
#         else:
#             style_str = 'style="'
#             style_str += " ".join([k+':'+v+';' for k, v in style_dict.items()])
#             style_str += '" '

#         styling_string = pTemplate('$classes$attributes$style').substitute({
#             "classes": class_str,
#             "attributes": attribute_str,
#             "style": style_str,
#         })

#         return styling_string

#     def render_styling_from_string_template(template):
#         # NOTE: We should add some kind of type-checking to template
#         """This method is a thin wrapper use to call `render_styling` from within jinja templates.
#         """
#         if type(template) != dict:
#             return template

#         if "styling" in template:
#             return render_styling(template["styling"])

#         else:
#             return ""

#     def render_string_template(template):
#         # NOTE: We should add some kind of type-checking to template
#         if type(template) != dict:
#             return template

#         if "styling" in template:

#             params = template["params"]

#             # Apply default styling
#             if "default" in template["styling"]:
#                 default_parameter_styling = template["styling"]["default"]

#                 for parameter in template["params"].keys():

#                     # If this param has styling that over-rides the default, skip it here and get it in the next loop.
#                     if "params" in template["styling"]:
#                         if parameter in template["styling"]["params"]:
#                             continue

#                     params[parameter] = pTemplate('<span $styling>$content</span>').substitute({
#                         "styling": render_styling(default_parameter_styling),
#                         "content": params[parameter],
#                     })

#             # Apply param-specific styling
#             if "params" in template["styling"]:
#                 # params = template["params"]
#                 for parameter, parameter_styling in template["styling"]["params"].items():

#                     params[parameter] = pTemplate('<span $styling>$content</span>').substitute({
#                         "styling": render_styling(parameter_styling),
#                         "content": params[parameter],
#                     })

#             string = pTemplate(template["template"]).substitute(params)
#             return string

#         return pTemplate(template["template"]).substitute(template["params"])


# class DefaultJinjaCmponentStylingInfo(object):
#     """Basically a struct type for:
#         {
#             **DomStylingInfo,
#             "header": DomStylingInfo,
#             "subheader": DomStylingInfo,
#             "body": DomStylingInfo,
#         }

#     EX: {
#             "classes": ["root_foo"],
#             "styles": {"root": "bar"},
#             "attributes": {"root": "baz"},
#             "header": {
#                 "classes": ["header_foo"],
#                 "styles": {"header": "bar"},
#                 "attributes": {"header": "baz"},
#             },
#             "subheader": {
#                 "classes": ["subheader_foo"],
#                 "styles": {"subheader": "bar"},
#                 "attributes": {"subheader": "baz"},
#             },
#             "body": {
#                 "classes": ["body_foo"],
#                 "styles": {"body": "bar"},
#                 "attributes": {"body": "baz"},
#             }
#         }
# """
#     pass
