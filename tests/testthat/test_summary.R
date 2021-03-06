context('Summary')

pv2 <- list(param = data.frame(p5 = c(-1, -2)),
            value = list(list(v3 = 'A',
                              v4 = 'B'),
                         list(v3 = 'C',
                              v4 = 'D')))

test_that('summary', {
    f <- function(param, value) {
        list(summary = data.frame(x = 1:10,
                                  y = 11:20,
                                  z = value$v3))
    }

    pv <- pvcall(f, pv2)
    s <- make_summary(pv)

    expect(is.data.frame(s))
    expect_equal(nrow(s), 10 * 2)
    expect_equal(colnames(s), c('p5', 'x', 'y', 'z'))
})
