# lazy-trader

This is a simple script designed to be run on a schedule that uses a supplied config file to figure out what stocks you should buy.

## config file explanation

The config file has two sections: `auth` and `allocation_map`:

- `auth` contains the currently valid refresh token.
- `allocation_map` contains a map of several classes of allocation.

Each allocation uses the same schema:

```yaml
bond: # the name of the allocation
    allocation: 10 # the target allocation percentage
    symbols: # a list of symbols you currently own that match this allocation (copy the next two lines for each new symbol)
    - currency: '' # the currency of the symbol
      symbol: '' # the ticker symbol (eg VCN.TO) <- Note you'll want the .TO for symbols that are also traded on the US exchange!
    buy: '' # which symbol to buy, should your account be behind your target allocation percentage. NOTE - This should be a symbol that exists in the `symbols` array, even if you don't own any of it, otherwise subsequent buys won't update your allocation!
```
## setup

Here's how to configure this app to work with your account: 

- Make a copy of the config.template.yaml file, name it `config.yaml`
- Enable API access on your questrade account
- Create a new app, generate a refresh token, paste that in `auth.refresh_token` in your `config.yaml`

Now for the time-consuming part. You're going to need to go through each of your questrade accounts, and research each ticker symbol to figure out which category you need to add it to. Make sure to add the currency as well as the ticker symbol

If it turns out that the categories in the yaml file don't make sense to you, you can create new ones - just make sure the category has the same schema.

## usage

### prerequisites

- A version of `python3`

### running the code

Follow these steps first:

- `python3 -m virtualenv venv`
- `source venv/bin/activate`
- `pip install -r requirements.txt`

To run the code, once you have set up `config.yaml`:

- Set up your mail account.
  - It's easiest to create a gmail account.
  - Follow [this guide](https://blog.macuyiko.com/post/2016/how-to-send-html-mails-with-oauth2-and-gmail-in-python.html) to create an API project for your gmail account. This is also where the code in `mail.py` comes from.
    NOTE - the "other" application type is now called "Desktop App".
  - create a `.env` file, add the id and secret on a new line each with the format `export GOOGLE_CLIENT_{ID | SECRET}={value}`
  - `python app/mail.py`
    - this will prompt you to authorize the app - you will have created a public app in test mode, and you'll have added your own email only to it so you can safely acknowledge that your app is not approved by google.
    - Following the prompts will generate a refresh token. Add this to the `.env` file using the same format.
  - in the ifmain block, replace the `___@gmail.com` with the to and from emails you will be using.
  - run `python app/mail.py` again -- this time you should get an email at the to address from the from address.
- Now you should be ready to run the actual app: `python app/main.py`.

## TODO
- dockerize project
- create makefile
- make it easy to set up auto scheduling with a cronjob