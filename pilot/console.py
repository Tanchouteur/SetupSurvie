"""Physical server access fallback; never exposed as a public recovery endpoint."""
import argparse
import asyncio
import getpass

from . import accounts, store


def main():
    parser=argparse.ArgumentParser(description='Secours local SetupSurvie — accès au PC serveur requis.')
    parser.add_argument('action',choices=['recovery-code','reset-password'])
    parser.add_argument('email')
    args=parser.parse_args()
    email=args.email.strip().lower()
    if '@' not in email:email+='@survie.local'
    if not (store.ROOT/'pilot.db').exists():store.init()
    account=accounts.native_account(email)
    if not account:parser.error('Compte introuvable.')
    if args.action=='reset-password':
        password=getpass.getpass('Nouveau mot de passe : ')
        if len(password)<8 or len(password.encode())>72:parser.error('Utilisez au moins 8 caractères et au plus 72 octets UTF-8.')
        if password!=getpass.getpass('Confirmer : '):parser.error('Confirmation différente.')
        asyncio.run(accounts.reset_password(email,password))
        print('Mot de passe remplacé ; anciennes sessions invalidées. Conversations conservées.')
    print('Nouveau code de secours à imprimer. Le précédent est invalidé :')
    print(store.recovery_code(account['id']))


if __name__=='__main__':main()
