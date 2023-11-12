# Route53 Record Collector

## Overview
This Python tool collects DNS records from AWS Route53 across multiple accounts using AWS SSO (Single Sign-On). It provides various options for listing, filtering, and analyzing the data.

## Requirements
- Python 3
- Install required packages using:
  ```bash
  pip install -r requirements.txt

## Usage


- Run accross all accounts
  - _With out using --accounts/-a, the tool will gather all accounts you have privilege to and fetch details of dns records. If you use --verbose/-v then it will show extra information you may need otherwise without --verbose/-v it will only show unique subdomains(record names)._
  ```python
  python route53_record_collector.py -u <SSO Start URL> -v
  
- Run accross selective account[s].
  ```python
  python route53_record_collector.py -u <SSO Start URL> -a <Account IDs> -v

- Filter record types.
  ```python
  python route53_record_collector.py -u <SSO Start URL> -a <Account IDs> -t <Record Type> -v

- Exclude record names using regex.
  ```python
  python route53_record_collector.py -u <SSO Start URL> -a <Account IDs> -e <Regex> -v

- Save output to a file.
  ```python
  python route53_record_collector.py -u <SSO Start URL> -a <Account IDs> -o <Output FileLocation> -v

- check if the record is dangling.
  ```python
  python route53_record_collector.py -u <SSO Start URL> -a <Account IDs> -cd -v
