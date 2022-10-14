import win32com.client

outlook = win32com.client.Dispatch('outlook.application')
mail = outlook.CreateItem(0)
mail.To = 'contact@company.com'
mail.Subject = 'Sample Email'
mail.HTMLBody = '<h3>This is HTML Body</h3>'
mail.Body = "This is the normal body"
mail.Attachments.Add('c:\\sample.xlsx')
mail.Attachments.Add('c:\\sample2.xlsx')
mail.CC = 'somebody@company.com'
mail.Send()


import win32com.client
#other libraries to be used in this vbs

'''
Like communicating with other system or app, you will need to initiate a session in the first place. By calling the GetNamespace function, you can get the outlook session for the subsequent operations.
'''
outlook = win32com.client.Dispatch('outlook.application')
mapi = outlook.GetNamespace("MAPI")

'''
if you have configured multiple accounts in your outlook, you need to pass in the account name when accessing it’s folders, we can cover this topic in another article. For this article, let assume we only have 1 account configured in outlook.
'''
for account in mapi.Accounts:
	print(account.DeliveryStore.DisplayName)

'''
To access the inbox folder, you will need to pass in the folder type – 6 in the below function. You may refer to this doc to understand the full list of folder types, such as the draft, outbox, sent, deleted items folder etc.
'''
