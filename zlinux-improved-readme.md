replace  the zlinux config\_preseed in zlinux from moshix

https://github.com/moshix/zlinux



make sure you have the post\_install\_modern.sh copied in







Next Steps



Create the directory if needed:



Bash

mkdir -p templates



Save both files exactly as above.



Make the new script executable:

Bash

chmod +x templates/post\_install\_modern.sh



Re-run the main installer:



Bash



./zlinux\_install.bash

