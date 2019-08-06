import React from 'react';
import Typography from '@material-ui/core/Typography';


export const footer = (classes) => <footer className={classes.footer}>
  <Typography variant="h6" align="center" gutterBottom>
    Otros Sitios de Interés
  </Typography>
  <Typography variant="subtitle1" align="center" color="textSecondary" component="p">
    Lista de enlaces
  </Typography>
</footer>