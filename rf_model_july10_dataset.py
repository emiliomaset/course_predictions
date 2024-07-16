import numpy
import sys
from sklearn.ensemble import RandomForestClassifier
from imblearn.ensemble import BalancedRandomForestClassifier
from sklearn.linear_model import LinearRegression
import numpy as np
from numpy import random
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import metrics
import seaborn as sns
from sklearn.metrics import confusion_matrix, recall_score
from sklearn.preprocessing import OrdinalEncoder
import warnings
from sklearn import tree
numpy.set_printoptions(threshold=sys.maxsize) #print entire numpy arrays

def preprocess_student_data(student_data):
    #student_data = student_data.drop_duplicates(subset=['SPRIDEN_PIDM'])
    student_data.reset_index(inplace=True, drop=True)

    return student_data

def create_features_matrix_and_target_vector_for_rf_model(student_data, training_course):
    indices_of_students_in_training_course = []

    is_in_course = np.zeros(shape=(len(student_data), 1))

    for i in range(0, len(student_data)):
        if str(student_data.iloc[i]["SPRIDEN_PIDM"]) in training_course["SPRIDEN_PIDM"].to_string():
            indices_of_students_in_training_course.append(i)
            is_in_course[i] = 1

    student_data["Enrolled in Course Next Year"] = is_in_course

    students_in_training_course = []
    for i in indices_of_students_in_training_course:
        students_in_training_course.append(student_data.iloc[i])

    target_vector = np.ones(shape=(len(students_in_training_course), 1))

    features_matrix = pd.DataFrame(students_in_training_course)
    features_matrix["Enrolled in Course Next Year"] = target_vector

    features_matrix = features_matrix._append(student_data.sample(n=len(features_matrix) * 1)) # make so only non-students are sampled?

    return features_matrix.drop(columns="Enrolled in Course Next Year"), np.array(features_matrix["Enrolled in Course Next Year"])

def create_features_matrix_for_rf_model(semester_data):
    semester_data.reset_index(inplace=True, drop=True)  # do i need?
    semester_data.drop(columns=semester_data.iloc[:, :5], inplace=True)
    semester_data = semester_data.iloc[:, :-6]

    return semester_data

def create_target_vector_for_rf_model(student_semester_data, student_next_semester_data, course_subject, course_number):
    target_vector = np.zeros(shape=(len(student_semester_data), 1))

    for i in range(0, len(student_semester_data)):
        if student_semester_data.iloc[i]["SPRIDEN_PIDM"] in student_next_semester_data["SPRIDEN_PIDM"].values:
            if len(student_next_semester_data[student_next_semester_data["SPRIDEN_PIDM"] == student_semester_data.iloc[i]["SPRIDEN_PIDM"]][course_subject + "_" + course_number].values) == 0:
                target_vector[i] = 0

            else:
                target_vector[i] = int(student_next_semester_data[student_next_semester_data["SPRIDEN_PIDM"] == student_semester_data.iloc[i]["SPRIDEN_PIDM"]][course_subject + "_" + course_number].values)

        else:
            target_vector[i] = 0

    return target_vector

def create_rf_model_for_course(all_student_data, course_subject, course_number):
    spring_2021_students_df = all_student_data.loc[
        (all_student_data["Academic Term"] == "Spring") & (all_student_data["Academic Year"] == "2020-2021")]

    fall_2021_students_df = all_student_data.loc[
        (all_student_data["Academic Term"] == "Fall") & (all_student_data["Academic Year"] == "2021-2022")]

    target_vector = create_target_vector_for_rf_model(spring_2021_students_df, fall_2021_students_df, course_subject, course_number)
    spring_2021_students_df = create_features_matrix_for_rf_model(spring_2021_students_df)

    zero_count = 0
    one_count = 0

    for i in range(0, len(target_vector)):
        if target_vector[i] == 1:
            one_count += 1
        else:
            zero_count += 1

    print(zero_count, one_count)

    random.seed(1234)
    rf_model = BalancedRandomForestClassifier(random_state=random.seed(1234), class_weight="balanced_subsample")
    rf_model.fit(spring_2021_students_df, target_vector)

    tree.plot_tree(rf_model);

    spring_2022_students_df = all_student_data.loc[
        (all_student_data["Academic Term"] == "Spring") & (all_student_data["Academic Year"] == "2021-2022")]

    fall_2022_students_df = all_student_data.loc[
        (all_student_data["Academic Term"] == "Fall") & (all_student_data["Academic Year"] == "2022-2023")]

    target_vector = create_target_vector_for_rf_model(spring_2022_students_df, fall_2022_students_df, course_subject, course_number)
    spring_2022_students_df = create_features_matrix_for_rf_model(spring_2022_students_df)


    zero_count = 0
    one_count = 0

    for i in range(0, len(target_vector)):
        if target_vector[i] == 1:
            one_count += 1
        else:
            zero_count += 1

    print(zero_count, one_count)

    y_pred = rf_model.predict(spring_2022_students_df)

    # threshold = 0.7
    #
    # predicted_proba = rf_model.predict_proba(fall_2021_students_df)
    # print(predicted_proba)
    # predicted = (predicted_proba[:, 1] >= threshold).astype('int')

    cm = confusion_matrix(target_vector, y_pred)
    cm_display = metrics.ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0, 1], )
    cm_display.plot()
    cm_display.figure_.set()
    plt.show()

    tn, fp, fn, tp = cm.ravel()
    sensitivity = tp / (tp + fn)
    specificity = tn / (tn + fp)
    print("Sensitivity:", sensitivity)
    print("Specificity:", specificity)

    spring_2022_students_df = all_student_data.loc[
        (all_student_data["Academic Term"] == "Spring") & (all_student_data["Academic Year"] == "2021-2022")]
    spring_2022_students_df.reset_index(inplace=True, drop=True)

    print(f"\n\nstudents in {course_subject} {course_number}")
    for i in range(0, len(target_vector)):
        if target_vector[i] == 1:
            print(spring_2022_students_df.iloc[i].to_frame().T.to_string()) # student in course

    print(f"\nstudents predicted to be in {course_subject} {course_number}")
    for i in range(0, len(target_vector)):
        if y_pred[i] == 1:
            print(spring_2022_students_df.iloc[i].to_frame().T.to_string())

    print(f"{int(sum(target_vector))} students from spring 2022 took the course in fall 2022. {tp} predictions were correct. there were {fp} false positives and {fn} false negatives.")

def main():
    # student_data = pd.read_excel("July 10 Dataset.xlsx")
    # pd.to_pickle(student_data, "July_10.pkl")

    student_data = pd.read_pickle("July_10.pkl")

    create_rf_model_for_course(student_data, "BSBA", "2209")

if __name__ == "__main__":
    main()