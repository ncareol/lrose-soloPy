from distutils.core import setup

#This is a list of files to install, and where
#(relative to the 'root' dir, where setup.py is)
#You could be more specific.
files = ["color_scales/*", "solopy_config.xml"]

setup(name = "lrose_solopy",
    version = "0.5",
    description = "Display CfRadial format radar/lidar file",
    author = "Xin Pan and Joe VanAndel",
    author_email = "vanandel@ucar.edu",
    url = "https://github.com/ncareol/lrose-soloPy",
    license = 'BSD'
    #Name the folder where your packages live:
    #(If you have other packages (dirs) or modules (py files) then
    #put them into the package directory - they will be found 
    #recursively.)
    packages = ['lrose_solopy'],
    #'package' package must contain files (see list above)
    #This dict maps the package name =to=> directories
    #It says, package *needs* these files.
    package_data = {'lrose_solopy' : files },
    #'start_pysolo' is in the root.
    scripts = ["run_solopy"],
    long_description = """Really long text here.""" 
    #
    #This next part it for the Cheese Shop, look a little down the page.
    #classifiers = []     
) 
