from flask import Flask
from flask import request
import subprocess
import re
import validators

app = Flask(__name__)

# Dear poor person looking at this code. I apologise.
# --Tomas

@app.route('/', methods=['GET', 'POST'])
def create_vms():
    def get_running_vms():
        vm_list = subprocess.check_output(['./get_running_vms.sh']).decode("utf-8").strip().split()
        return f'{len(vm_list)} VMs running. <a href="/manage">Manage</a>'

    def get_status():
        wget = subprocess.check_output(['./get_running_process_count.py', 'wget']).decode("utf-8").strip()
        virt_install = subprocess.check_output(['./get_running_process_count.py', 'virt-install']).decode("utf-8").strip()

        if wget != "2":
            return "<div>An image is being downloaded</div>"
        elif virt_install != "2":
            return "<div>The VM(s) are being created</div> <br/>"
        return ""

    def start_vms_on_background(url, num_of_nodes, prefix):
        subprocess.Popen(['./runner.sh', url, num_of_nodes, prefix])

    refresher = """
        <head>
            <title>Node Creator 4000</title>
            <meta http-equiv="refresh" content="5">
        </head>
    """

    title = """
        <head>
            <title>Node Creator 4000</title>
        </head>
    """
    dont_resubmit = """
        <script>
        if ( window.history.replaceState ) {
            window.history.replaceState( null, null, window.location.href );
        }
        </script>
    """

    submit_form = """
        <div>
            <form action="/" method="post" id="vm_create_form">
                <label for="url">Paste the discovery iso URL into this box</label>
                <br />
                <textarea id="url" name="url" rows="4" cols="150"></textarea>
                <br />
                <label for="numofnodes">Number of nodes you want to create</label>
                <br />
                <input type="text" id="numofnodes" name="numofnodes" value="3">
                <br />
                <label for="nodes-prefix">Optional prefix (not visible to user anywhere, just helps to manage the resources)</label>
                <br />
                <input type="text" id="nodes-prefix" name="node-prefix" value="">

            </form>
            <button type="submit" form="vm_create_form" value="Submit">Submit</button>
        <div>
        <br />
    """

    div = submit_form + get_running_vms()
    status = get_status()
    in_progress_message = "Host creation in progress. Please wait until the process finished before submitting a next request. Current status: " + status

    if status != "":
        div = in_progress_message + refresher
    if request.method == 'POST':
        if get_status() != "":
            return in_progress_message + dont_resubmit + refresher

        num_of_nodes = request.form['numofnodes'].strip()
        if num_of_nodes == "":
            num_of_nodes = "3"
        elif not num_of_nodes.isnumeric():
            return "The number of nodes have to be a number" + dont_resubmit + title

        url = request.form['url']
        url = url.strip()
        if url.startswith('wget'):
            url = re.sub(r"wget -O .*\.iso '", '', url)[:-1]

        if url == "":
            return "The URL can not be empty" + dont_resubmit + title
        if not validators.url(url):
            return "The provided URL is not an actual URL" + dont_resubmit + title

        prefix = request.form['node-prefix']
        if prefix != "":
            prefix = prefix.replace(" ", "")

        if prefix == "":
            prefix = "unset"

        start_vms_on_background(url, num_of_nodes, prefix)
        return "<div>The host creation has been submitted. The hosts should start showing up in the wizard in few minutes</div><br /> Current status: " + get_status() + dont_resubmit + refresher
    else:
        return div + title

@app.route('/manage', methods=['GET', 'POST'])
def manage_vms():
    def delete_vms_on_background(vms):
        subprocess.run(['./delete_vms.sh'] + vms)

    def get_running_vms():
        form_header = """
            <form action="/manage" method="post" id="vm_delete_form">
        """
        form_footer = """
            <br /> <button type="submit" form="vm_delete_form" value="Submit">Delete selected VMs</button>
        </form>
        """

        vm_list = subprocess.check_output(['./get_running_vms.sh']).decode("utf-8").strip().split()
        vm_checkboxes = [f'<input type="checkbox" id="{vm}" name="vmname" value="{vm}"><label for="{vm}">{vm}</label>'  for vm in vm_list]
        vms_joined = "<br />".join(vm_checkboxes)

        return form_header + vms_joined + form_footer

    back_button = """
        <br/ > Back <a href="/">Back</a>
    """

    if request.method == 'POST':
        vm_list = request.form.getlist('vmname')
        if (len(vm_list) > 0):
            delete_vms_on_background(vm_list)

    return get_running_vms() + back_button