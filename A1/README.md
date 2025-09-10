## A1



##### Problem Identification



* I chose student depression and its factors
* The target variable I aimed to predict is if a student does or doesn't have 'Depression'





##### Data Collection



* I selected this dataset from Kaggle: [https://www.kaggle.com/datasets/hopesb/student-depression-dataset](https://www.kaggle.com/datasets/hopesb/student-depression-dataset)





##### Model Development



I chose Random Forest and SVM models from scikit-learn.





##### Model Evaluation



ACCURACY~

RF: 0.7868

SVM: 0.8337





SVM demonstrates that it is better suited for this dataset than RF most likely because RF excels in non-linear datasets, thus indicating that SVM is more suited for linear datasets. Such is the case here as with an increase or decrease of the independent variables in turn affects whether a student has depression.





##### Documentation and Code Submission



* The code pre-processes the dataset which is easier to teach the models. 
* The dataset is then categorized as input data (independent features) and output data (target variable)
* Data was split into 80% to train and 20% to test
* Models: RF and SVM were used
