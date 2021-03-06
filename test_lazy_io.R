devtools::load_all()

options(paramvalf_lazy_threshold = 0)

bootstrap_param <- list(param = data.frame(boot_l = c(1, 2, 4)))
matrixfit_model <- list(param = data.frame(model = c('shifted', 'weighted')))

len <- 100

.func <- function (param, value) {
    list(foo = 1:len,
         bar = 2:len)
}
pv_call('.', pv1, .func, bootstrap_param, matrixfit_model)
#pv_save('.', pv1)

.func <- function (param, value) {
    list(baz = 3:len)
}
pv_call('.', pv2, .func, bootstrap_param)
#pv_save('.', pv2)

pv_load('.', pv1)
pv_load('.', pv2)

.func <- function (param, value) {
    list(res = 4:len,
         res2 = value$baz)
}
pv_call('.', pv3, .func, pv2, matrixfit_model, serial = TRUE)
#pv_save('.', pv3)

#debug_print(pv3)

rm(pv3)

pv_load('.', pv3, eager = TRUE)

#debug_print(sapply(pv3$value, function (x) length(x$res)))
#debug_print(sapply(pv3$value, function (x) length(x$res2)))

#debug_print(pv3)
