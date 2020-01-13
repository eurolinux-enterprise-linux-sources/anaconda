package = anaconda
package_version_tar = $(shell spectool -l $(package).spec | grep Source0 |  awk -FSource0: '{print $$2}' | sed -e 's/^[ \t]*//')
package_version = $(shell echo $(package_version_tar) | awk -F.tar '{print $$1}')


sources:
	for i in $(find ./src/ -type f -empty -print | grep .gitkeep);do echo "removing $i"; rm -f $i; done
	cp -a src $(package_version) \
	&& tar czvvf $(package_version_tar) $(package_version)/ \
	&& rm -rf $(package_version)
	for i in $(find ./src/ -type d -empty -print);do echo "$i/.gitkeep"; touch $i/.gitkeep; done
