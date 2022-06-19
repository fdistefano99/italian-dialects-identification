from transformers import AdamW, get_linear_schedule_with_warmup
import torch

def train(model, 
         device : str, 
         train_dataloader, 
         val_dataloader=None, 
         epochs=4, 
         evaluation=False):
    """
    Train the model.
    """

    print("Start training...\n")

    optimizer = AdamW(model.parameters(), lr=5e-5, eps=1e-8)
    total_steps = len(train_dataloader) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=0, num_training_steps=total_steps)

    for epoch_i in range(epochs):

        total_loss = 0

        # model in training mode
        model.train()

        # iterate over batches
        for batch in train_dataloader:

            input_ids, attention_mask, labels = tuple(t.to(device) for t in batch)

            # zero out any previous gradients
            model.zero_grad()

            # perform a forward pass, that returns the CLS token for every input sentence
            cls_tokens = model.forward(input_ids=input_ids, attention_mask=attention_mask)

            # compute loss and accumulate the loss values
            loss = model.loss_fn(cls_tokens, labels)
            total_loss += loss.item()

            # perform a backward pass to calculate gradients
            loss.backward()

            # clip the norm of the gradients to 1.0 to prevent "exploding gradients"
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

            # Update parameters and the learning rate
            optimizer.step()
            scheduler.step()


        # Calculate the average loss over the entire training data
        avg_train_loss = total_loss / len(train_dataloader)

        print("-"*70)
        # =======================================
        #               Evaluation
        # =======================================
        if evaluation == True:

            val_loss, val_accuracy = evaluate(model, val_dataloader)
            print(f" Epoch {epoch_i + 1:^7} | {'-':^7} | {avg_train_loss:^12.6f} | {val_loss:^10.6f} | {val_accuracy:^9.2f}")
            print("-"*70)
        print("\n")
    
    print("Training complete!")


def evaluate(model, val_dataloader):
    """After the completion of each training epoch, measure the model's performance
    on our validation set.
    """
    # Put the model into the evaluation mode. The dropout layers are disabled during
    # the test time.
    model.eval()

    # Tracking variables
    val_accuracy = []
    val_loss = []

    # For each batch in our validation set...
    for batch in val_dataloader:
        
        # Load batch to GPU
        b_input_ids, b_attn_mask, b_labels = tuple(t.to(device) for t in batch)

        # Compute logits
        with torch.no_grad():
            logits = model(b_input_ids, b_attn_mask)

        # Compute loss
        loss = loss_fn(logits, b_labels)
        val_loss.append(loss.item())

        # Get the predictions
        preds = torch.argmax(logits, dim=1).flatten()

        # Calculate the accuracy rate
        accuracy = (preds == b_labels).cpu().numpy().mean() * 100
        val_accuracy.append(accuracy)

    # Compute the average accuracy and loss over the validation set.
    val_loss = np.mean(val_loss)
    val_accuracy = np.mean(val_accuracy)

    return val_loss, val_accuracy



