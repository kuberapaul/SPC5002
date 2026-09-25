The leaked column was `export_seq`.

It scored far above the other columns when tested on its own because it is not an ordinary customer feature. It is a record of the export process itself, which means it carries information about the order after the system has already decided how to handle it. In practice, this column is created as part of the operational workflow: rows are numbered or sequenced as they are exported, and that sequence is later tied to the business outcome. That makes it a form of time- or processing-order leakage. It is not something the model was supposed to know before predicting whether a customer would return an item.

The mechanism matters: the model saw a value that was created by the pipeline itself, not by the customer or by the event we were trying to predict. Once that sequence is present, it effectively leaks information about the row’s place in the export and about how the underlying operations handled the order. That is why the score is inflated and why the column is not legitimate in a real prediction setup.

The notebook checks would catch this in different ways. The train/test split would not help by itself, because the leakage is still present in both sets. The scaler would also not help, since it only rescales numeric features and does not remove a bad column. The metric would show an unrealistically strong score, which is exactly what makes the issue visible. The missing check is the one in the homework: a deliberate scan of each column and a question about whether the value would have been known at prediction time.

A five-fold cross-validation would not solve it, because the same leakage pattern would still be present in each fold. The problem is not variance or overfitting; it is that the model is being given information that would not exist in a realistic prediction problem. The right question is: “Would we know this value at the moment we need to make the prediction?” For `export_seq`, the answer is no.

That is why it must be removed.
