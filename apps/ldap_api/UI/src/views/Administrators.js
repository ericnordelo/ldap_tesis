import  React, { Component } from 'react'
import Breadcrumbs from '@material-ui/lab/Breadcrumbs';
import {Link} from 'react-router-dom';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import Typography from '@material-ui/core/Typography';
import config from '../config';
import CircularIndeterminated from '../components/CircularIndeterminated';
import IconButton from '@material-ui/core/IconButton';
import DeleteIcon from '@material-ui/icons/Delete';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemSecondaryAction from '@material-ui/core/ListItemSecondaryAction';
import ListItemText from '@material-ui/core/ListItemText';
import Button from '@material-ui/core/Button';
import AddAdminDialog from '../components/AddAdminDialog';

class Administrators extends Component {
  state = { 
    admins: [], 
    loading: true,
    loading2: false,
    name: '',
    last_name: '',
    email: '',
  };

  constructor(props){
    super(props);
    this.fetchData = this.fetchData.bind(this);
    this.addAdmin = this.addAdmin.bind(this);
  }

  componentDidMount() {
    this.fetchData();
  }

  fetchData(){
    this.setState({loading: true});
    fetch(config.api_address + '/administradores', {credentials: "include"})
      .then(results => results.json())
      .then(data => {
        const ldap_admins = data.administradores;
        if(ldap_admins){
          this.setState({ admins: ldap_admins });
        }
        else{
          alert('No se pudieron obtener los administradores del API.');
        }
        this.setState({loading: false});
      }).catch(err => {
        console.log(err);
        this.setState({loading: false});
      })
  }

  addAdmin(email){
    this.setState({loading2: true});
    fetch(config.api_address + '/administradores', {
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: "include",
      method: 'PUT',
      body: JSON.stringify({email: email}),
      })
      .then(results => results.json())
      .then(data => {
        if(data.success){
          let admins = this.state.admins;
          admins.push({email: email});
          this.setState({loading2: false, admins: admins});
          alert(data.success)
        }else{
          alert(data.error)
        }
      }).catch(err => {
        this.setState({loading2: false});
      })
  }

  render() {
    
    return (
      <div>
        <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} arial-label="Breadcrumb">
          <Link color="inherit" to="/">
            Inicio
          </Link>
          <Typography color="textPrimary">Administradores</Typography>
        </Breadcrumbs>

        {this.state.loading ?
          <CircularIndeterminated/> :  this.state.admins.length > 0 ? 
            <div style={{backgroundColor: 'white', marginTop: 30}}>
            <List>
            { this.state.admins.map(function(admin) {
                return <ListItem>
                <ListItemText
                  primary={admin.email}
                />
                <ListItemSecondaryAction>
                  <IconButton edge="end" aria-label="delete">
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
              })
            }
            </List>
            </div> : 
            <div style={{backgroundColor: 'white', marginTop: 30, padding: 20}}>
              No hay administradores.
            </div>
        }

        <AddAdminDialog email={this.state.email} addMethod={this.addAdmin}/>

      </div>
    );
  }
}

export default Administrators;