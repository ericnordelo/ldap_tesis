import React from 'react';
import Typography from '@material-ui/core/Typography';


export const footer = (classes) => <footer className={classes.footer}>
  <Typography variant="h6" align="center" gutterBottom>
    Otros Sitios de Interés
  </Typography>
  <Typography variant="subtitle1" align="center" color="textSecondary" component="p">
    <a href="http://correo.uh.cu" target="blank">correo.uh.cu</a>
  </Typography>
  <Typography variant="subtitle1" align="center" color="textSecondary" component="p">
    <a href="http://proxy.uh.cu/cuotas" target="blank">proxy.uh.cu/cuotas</a>
  </Typography>
  <Typography variant="subtitle1" align="center" color="textSecondary" component="p">
    <a href="http://intranet.uh.cu" target="blank">intranet.uh.cu</a>
  </Typography>
  <Typography variant="subtitle1" align="center" color="textSecondary" component="p">
    <a href="http://www.uh.cu" target="blank">www.uh.cu</a>
  </Typography>
</footer>