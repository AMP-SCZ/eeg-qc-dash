# eeg-qc-dash

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6326487.svg)](https://doi.org/10.5281/zenodo.6326487) [![Python](https://img.shields.io/badge/Python-3.6-green.svg)]() [![Platform](https://img.shields.io/badge/Platform-linux--64-orange.svg)]()


Billah, Tashrif; Bouix, Sylvain; Nicholas, Spero; Mathalon, Daniel; Light, Gregory;
Plotly/Dash based web application for checking quality of EEGs,
https://github.com/AMP-SCZ/eeg-qc-dash/, 2022, DOI: 10.5281/zenodo.6326487



uWSGI was installed according to [official documentation](https://uwsgi-docs.readthedocs.io/en/latest/WSGIquickstart.html):

```bash
wget https://projects.unbit.it/downloads/uwsgi-latest.tar.gz
tar -zxvf uwsgi-latest.tar.gz
cd uwsgi-*
export PATH=~/miniconda3/bin/:$PATH
make
```

Notice that we used the main Python for uWSGI install, not an environment Python.
The latter does not have one dynamic library that is required to link with uWSGI.
Accordingly, you should run `pip install -r eeg-qc-dash/requirements.txt` on the main Python.


export DASH_DEBUG=False
export DASH_URL_BASE_PATHNAME=/eegqc/
export EEG_QC_PHOENIX=/data/predict/data_from_nda/
export PATH=~/uwsgi-2.0.20/:~/miniconda3/bin/:$PATH
export PYTHONHOME=~/mininconda3/
cd ~/eegqc-dash/



### Launch uwsgi-nginx in http protocol

In this method, Nginx speaks http protocol to uWSGI. It can be slow.

#### nginx.conf
```cfg
    location /eegqc/ {
      proxy_pass http://localhost:8050/;
    }
```

#### uwsgi

> uwsgi --http :8050 --wsgi-file wsgi.py --master --processes 1 --threads 1





### Launch uwsgi-nginx in wsgi protocol

In this method, Nginx speaks wsgi protocol to uWSGI. It is fast.

References: [digitalocean](https://www.digitalocean.com/community/tutorials/how-to-set-up-uwsgi-and-nginx-to-serve-python-apps-on-ubuntu-14-04)
and [uwsgi-docs](https://uwsgi-docs.readthedocs.io/en/latest/Nginx.html#configuring-nginx)

#### Using port (slower)

```cfg
    location /eegqc/ {
      include uwsgi_params;
      uwsgi_pass 127.0.0.1:8050;
    }
```

> $ uwsgi --socket :8050 --wsgi-file wsgi.py --master --processes 1 --threads 1

#### Using socket (fastest)

The following section was added to `/etc/nginx.conf`:

```cfg
    location /eegqc/ {
      include uwsgi_params;
      uwsgi_pass unix:///run/uwsgi.sock;
    }
```

And uWSGI server was launched as follows:

> $ uwsgi --socket /run/uwsgi.sock --wsgi-file uwsgi.py --master --processes 1 --chmod-socket=666


`/tmp/uwsgi.sock` could not be discovered by Nginx apparently because of [this](https://serverfault.com/a/464025) issue.
So we used `/run/uwsgi.sock`. Now it could be discovered ut SELinux prevented Nginx from writing into it:

```bash
$ tail -f /var/log/messages
Oct 25 15:15:39 rc-predict setroubleshoot: SELinux is preventing nginx from connectto access on the unix_stream_socket /run/uwsgi.sock. For complete SELinux messages run: sealert -l 262f5c36-68ca-4eeb-a9ff-661a2f94a64e
```

To circumvent this permission deficit, we had to add a policy to SELinux according to [*Extend the httpd_t Domain Permissions*](https://www.nginx.com/blog/using-nginx-plus-with-selinux/).

The `httpd_can_network_connect` bool was set to 1 as usual.
