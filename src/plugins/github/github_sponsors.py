import requests
import logging
logger =logging .getLogger (__name__ )
GRAPHQL_QUERY ="""запрос ($ имя пользователя: строка!) {
  пользователь (логин: $username) {
    спонсорствоAsMaintainer(first: 100) {
      общее количество
      узлы {
        создано в
        спонсорEntity {
          ... на пользователя {
            войти
            имя
          }
          ... об организации {
            войти
            имя
          }
        }
        уровень {
          имя
          ежемесячноЦенавцентах
        }
      }
    }
    расчетныйСледующийСпонсорыВыплатыInCents
  }
}"""
def sponsors_generate_image (plugin_instance ,settings ,device_config ):
    dimensions =device_config .get_resolution ()
    if device_config .get_config ("orientation")=="vertical":
        dimensions =dimensions [::-1 ]
    api_key =device_config .load_env_key ("GITHUB_SECRET")
    if not api_key :
        raise RuntimeError ("Ключ API GitHub не настроен.")
    github_username =settings .get ("githubUsername")
    if not github_username :
        raise RuntimeError ("Требуется имя пользователя GitHub.")
    data =fetch_sponsorships (github_username ,api_key )
    total_per_month =calculate_monthly_total (data )
    template_params ={
    "username":github_username ,
    "total_per_month":total_per_month ,
    "plugin_settings":settings
    }
    return plugin_instance .render_image (
    dimensions ,
    "github_sponsors.html",
    "github.css",
    template_params
    )
def fetch_sponsorships (username ,api_key ):
    url ="https://api.github.com/graphql"
    headers ={"Authorization":f"Bearer {api_key }"}
    variables ={"username":username }
    resp =requests .post (url ,json ={"query":GRAPHQL_QUERY ,"variables":variables },headers =headers )
    resp .raise_for_status ()
    data =resp .json ()
    if "errors"in data :
        raise RuntimeError (f"GitHub API returned errors: {data ['errors']}")
    logger .debug (f"Fetched sponsor data for {username }: {data }")
    return data
def calculate_monthly_total (data )->int :
    sponsorships =data ['data']['user']['sponsorshipsAsMaintainer']['nodes']
    total_per_month =sum (s ['tier']['monthlyPriceInCents']/100 for s in sponsorships )
    return int (total_per_month )