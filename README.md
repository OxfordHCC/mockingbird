# Mockingbird
This repository contains the code for my Master's of Science Dissertation completed at the University of Oxford.

The directory `mockingbird` contains the code used to build the Mockingbird tool (available at [mockingbird.hip.cat](http://mockingbird.hip.cat/)). This code will not run directly as the pre-trained classifiers are not included with the repository and the SQLite database has been deleted to ensure no sensitive information is shared. Use the Djano commands `makemigrations` and `migrate` to initialize a new database. Additionally, the key for the [IBM Personality Insights API](https://personality-insights-demo.ng.bluemix.net/) have been removed. A new one can be added in the file `twitter/profile_builders.py`. Otherwise the code should be ready to run using Django. A sample account called `test` is provided to check the functionality of the profiling tools without scraping a Twitter account. To scrape tweets, I used a modified version of the Twint tool, available [here](https://github.com/ahare63/twint).

The directory `docs` includes several documents relevant to the project, including a pdf of the final report.

The directory `models` includes a few files outlining how the various neural networks were trained and some of the code used to adapt the A^4NT model, the original code for which is available [here](https://github.com/rakshithShetty/A4NT-author-masking).
