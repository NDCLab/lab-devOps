#!/bin/bash
setfacl -Rm mask:rwx,user::rwx,other:--- /home/data/NDClab && \
setfacl -Rdm mask:rwx,user::rwx,other:--- /home/data/NDClab

