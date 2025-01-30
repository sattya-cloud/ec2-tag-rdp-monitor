# ec2-tag-rdp-monitor
1. We need to build remediation script in which we need check whether in EC2s instances are there two tags are mandatorily defined 1. Business Unit 2. ITSO EMail. 
After this we need to check if someone mistakenly opened RDP port to internet i.e 0.0.0.0/0 then ITSO should recieve a warning email suggesting to check EC2 in which he/she has defined RDP open to internet i.e 0.0.0.0/0
2. If any EC2 instance stops in production then your ITSO should recieve a warning email.
