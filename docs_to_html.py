import argparse
from markdown import markdown


def findnth(haystack, needle, n):
    parts = haystack.split(needle, n+1)
    if len(parts) <= n+1:
        return -1
    return len(haystack)-len(parts[-1])-len(needle)


def docs_to_html(output_file):
    rdme = './README.md'

    # initialize with the start of the static block
    html_out = [
        "{% extends \"images/base.html\" %}",
        "{% load static %}",
        "{% block content %}"
    ]
    with open(rdme) as f:
        for line in f:

            if "For Developers" in line:
                break

            if "<img src=" in line:
                first_quote, second_quote = findnth(line, "\"", 0), findnth(line, "\"", 1)
                im_name = line[first_quote+1:second_quote]
                im_name_html = im_name.replace('./', 'images/')
                im_name_html = "{% static '" + im_name_html + "' %}"
                line = line.replace(im_name, im_name_html)

            html_out.append(markdown(line))

    html_out = "\n".join(html_out)
    # add end of the static block
    html_out += "{% endblock content %}\n"

    with open(output_file, 'w') as f:
        f.write(html_out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    default_out = '../embl-annotation-service/templates/images/about.html'
    parser.add_argument('--out_file', type=str, default=default_out)
    args = parser.parse_args()
    docs_to_html(args.out_file)
