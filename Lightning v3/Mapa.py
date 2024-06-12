import streamlit as st
import pyodbc
import pandas as pd
from datetime import datetime,time
import datetime as dates
import pytz
import time
import leafmap.foliumap as leafmap
import folium
import streamlit_folium
from streamlit_autorefresh import st_autorefresh
import random
import branca
newYorkTz = pytz.timezone("America/New_York")
# Initialize connection.
# Uses st.cache_resource to only run once.
st.set_page_config(layout="wide")
timer = st.empty()

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.

# def run_query(query,_conn):
#     return pd.read_sql(query, _conn)
# stationinfo={}
# stationinfo2={}
# stationinfo3={}
# with open('stations.txt','r') as file:
#     temp = file.read()
#     lines = temp.split('\n')
#     for line in lines:
#         data = line.split("\t")
#         if len(data)>4:
#             stationinfo[data[0]]=data
#             stationinfo2[float(data[4])]=data[0]
#             stationinfo3[float(data[4])]=float(data[3])
# meta = pd.read_xml("AWSMetadata.xml")
unit = st.sidebar.selectbox("Formato de tiempo",["Tiempo real","Horario"])
if unit == "Horario":
    date = st.sidebar.date_input("Fecha",min_value=datetime(2000,1,1),max_value=datetime.now(),value=datetime(datetime.now().year,1,1))
    hour1 = st.sidebar.time_input("Hora inicial",value=dates.time(hour=0),step=3600)
    hour2 = st.sidebar.time_input("Hora final",value=dates.time(hour=23),step=3600)
datatype = st.sidebar.selectbox("Tipo de datos",["Rayos","Pulsos"])
dtype = "ltype"
if datatype=="Pulsos":
    dtype="ptype"
typeform = st.sidebar.multiselect("Clasificación",["IC","CG"],default=["IC","CG"])
bigger = st.sidebar.number_input("Amperaje superior a:",value=-100000,step=5000)
smaller = st.sidebar.number_input("Amperaje inferior a:",value=100000,step=5000)
higher  = st.sidebar.number_input("Altura superior a:",value=0,step=2000)
lower  = st.sidebar.number_input("Altura inferior a:",value=20000,step=2000)
# Initialize connection.


if 'map' not in st.session_state:
    st.session_state.map = leafmap.Map(center=[22, -79], zoom_start=6)
m = folium.Map(center=[22, -79], zoom_start=6)


conn = st.connection("postgresql", type="sql")

    # Perform query.
if unit == "Horario":
    table = "Flash"
    if datatype == "Pulsos":
        table="Pulse"
    initdate = datetime(date.year,date.month,date.day,hour1.hour,0,0)
    findate = datetime(date.year,date.month,date.day,hour2.hour,59,59)
    query = f"SELECT * FROM {table} Where id_date >= '{initdate}' and id_date<='{findate}';"
    df = conn.query(query, ttl="10m")
else:
    table = "Flash"
    if datatype == "Pulsos":
        table="Pulse"
    initdate = datetime.now()-dates.timedelta(minutes=5)
    findate = datetime.now()
    query= f"SELECT * FROM {table} Where id_date >= '{initdate}' and id_date<='{findate}';"
    df = conn.query(query, ttl="10m")

file = df

lightning = "C:\\Users\\albertoh\\Downloads\\flash.csv"
# file =pd.read_csv(lightning)
# rand=random.randrange(0,len(file))
# for i in range(rand):
#     file=file.drop(i)
file=file.loc[file[dtype].isin([0,1])]
file=file[(file["longitude"]<=-73) & (file["longitude"]>=-85)]
file=file[(file["latitude"]<=23.2) & (file["latitude"]>=19.5)]
if "IC" not in typeform:
        file=file.loc[file[dtype]!=1]
if "CG" not in typeform:
    file=file.loc[file[dtype]!=0]
file=file.loc[file["peakcurrent"]>=bigger]
file=file.loc[file["peakcurrent"]<=smaller]
file=file.loc[file["icheight"]>=higher]
file=file.loc[file["icheight"]<=lower]
keys = {'id_date':"Fecha","ltype":'Tipo',"ptype":'Tipo',"latitude":"Latitud","longitude":"Longitud","icheight":"Altura IC(m)","peakcurrent":"Intensidad máxima(A)","icmulti":"Cantidad IC","cgmulti":"Cantidad CG","sensor":"# de Sensores"}
file.rename(columns=keys,inplace=True)
file["Tipo"][file["Tipo"]==1]="IC"
file["Tipo"][file["Tipo"]==0]="CG"
file = file.drop("id",axis=1)
if datatype == "Pulsos":
    file = file.drop("major",axis=1)
    file = file.drop("minor",axis=1)
    file = file.drop("bearing",axis=1)
    file = file.drop("id_flash",axis=1)
if len(file)==0:
    st.info("La consulta realizada no contiene datos.")
def process_data(df):
    loc = df[["Latitud","Longitud"]]
    pop = []
    icons = []
    for row in df.itertuples(index=False, name=None):
        temp = ""
        color= ""
        for k,v in enumerate(row):
            if df.columns.values[k]=="Tipo":
                if v == "IC":
                    color="blue"
                else:
                    color="red"
            if df.columns.values[k]=="Intensidad máxima(A)":
                if int(v)>0:
                    if color== "red":
                        color = "black"
                    if color== "blue":
                        color = "lightblue"
            a= "<b>{0}:</b>".format(df.columns.values[k])
            b=" {0}".format(v)
            temp+=a+b+' <br> '
        icons.append(color)
        temp+=""
        pop.append(temp)
    pop=[folium.Popup(branca.element.IFrame(html=x,width=200, height=200),parse_html=True,max_width=200) for x in pop]
    icons=[folium.CustomIcon(icon_image="flash-"+x+".png",icon_size=(40,40)) for x in icons]
    #icons = [folium.Icon(color=x,icon="flash","icon_size:[20,20]") for x in icons]
    return (loc,pop,icons)
loc,pop,icons = process_data(file)
num = file["Tipo"].nunique()
    # m.add_geojson(regions, layer_name='US Regions')
fg = folium.FeatureGroup(name="State bounds")

if len(loc) == 0:
    loc=None
    pop=None
    icons=None
mk = folium.plugins.marker_cluster.MarkerCluster(locations=loc,control=True,popups=pop,icons=icons,name="Marker Cluster")
fg.add_child(mk)
folium.plugins.draw.Draw(export=True).add_to(m)
folium.plugins.Fullscreen().add_to(m)

# m.add_points_from_xy(
#             file,
#             x="Longitud",
#             y="Latitud",
#             color_column="Tipo",
#             icon_names=['fa-bolt']*num,
#             spin=True,
#             add_legend=True,
#         )

kk=streamlit_folium.st_folium(m,center=[22, -79], zoom=6,feature_group_to_add=fg,use_container_width=True,returned_objects=[])


if unit == "Tiempo real":
    if True:
        
        count = st_autorefresh(interval=1*60*1000)
        #st.rerun()

print("lol")
